'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  AlertTriangle,
  Clock,
  MapPin,
  Users,
  ShieldCheck,
  Radio,
  Zap,
  TrendingUp,
  Search,
  Loader2,
  CheckCircle2,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import type { TriageEntry, ManifestEntry, SystemStatus } from '@/lib/types';

const statusConfig = {
  critical: {
    label: 'Critical',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    glow: 'neon-border-red',
    badge: 'bg-red-500/20 text-red-400 border-red-500/40',
    dot: 'bg-red-500',
  },
  high: {
    label: 'High',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    glow: '',
    badge: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
    dot: 'bg-orange-500',
  },
  moderate: {
    label: 'Moderate',
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    glow: '',
    badge: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
    dot: 'bg-yellow-500',
  },
  low: {
    label: 'Low',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    glow: 'neon-border-emerald',
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
    dot: 'bg-emerald-500',
  },
} as const;

function getRankGlow(rank: number) {
  if (rank === 1) return 'neon-border-red';
  if (rank === 2) return 'neon-border-red';
  if (rank === 3) return 'neon-border-cyan';
  return '';
}

function getRankBadgeClass(rank: number) {
  if (rank <= 2) return 'bg-red-500/25 text-red-300 border-red-500/50 neon-text-red';
  if (rank <= 4) return 'bg-orange-500/20 text-orange-300 border-orange-500/40';
  if (rank <= 6) return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40';
  return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
}

export default function Dashboard() {
  const [triage, setTriage] = useState<TriageEntry[]>([]);
  const [manifest, setManifest] = useState<ManifestEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('operational');
  const [currentTime, setCurrentTime] = useState('');

  const [selectedHabitation, setSelectedHabitation] = useState<string>('');
  const [authorizedBy, setAuthorizedBy] = useState('');
  const [authorizing, setAuthorizing] = useState(false);
  const [authResult, setAuthResult] = useState<{ success: boolean; message: string } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [triageRes, manifestRes] = await Promise.all([
        fetch('/api/triage'),
        fetch('/api/manifest'),
      ]);
      const triageData: TriageEntry[] = await triageRes.json();
      const manifestData: ManifestEntry[] = await manifestRes.json();
      setTriage(triageData);
      setManifest(manifestData);

      const criticalCount = triageData.filter((t) => t.status === 'critical').length;
      if (criticalCount >= 2) setSystemStatus('critical');
      else if (criticalCount >= 1 || triageData.some((t) => t.ttiHours < 3)) setSystemStatus('degraded');
      else setSystemStatus('operational');
    } catch (err) {
      setSystemStatus('degraded');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('en-US', { hour12: false }) +
        ' UTC · ' +
        now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const totalHabitations = triage.length;
  const highRiskCount = triage.filter((t) => t.status === 'critical' || t.status === 'high').length;
  const avgTTI = totalHabitations > 0 ? triage.reduce((sum, t) => sum + t.ttiHours, 0) / totalHabitations : 0;
  const totalPopulation = triage.reduce((sum, t) => sum + t.population, 0);

  const filteredTriage = triage.filter(
    (t) =>
      t.habitationName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAuthorize = async () => {
    if (!selectedHabitation || !authorizedBy.trim()) return;
    setAuthorizing(true);
    setAuthResult(null);
    try {
      const res = await fetch('/api/manifest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ habitationId: selectedHabitation, authorizedBy: authorizedBy.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setAuthResult({ success: true, message: data.message });
        setManifest((prev) =>
          prev.map((m) =>
            m.id === selectedHabitation
              ? { ...m, authorized: true, authorizedBy: authorizedBy.trim(), authorizedAt: new Date().toISOString() }
              : m
          )
        );
        setSelectedHabitation('');
        setAuthorizedBy('');
      } else {
        setAuthResult({ success: false, message: data.error || 'Authorization failed' });
      }
    } catch (err) {
      setAuthResult({ success: false, message: 'Network error during authorization' });
    } finally {
      setAuthorizing(false);
    }
  };

  const statusInfo = {
    operational: { label: 'All Systems Operational', color: 'text-emerald-400', dot: 'bg-emerald-400', glow: 'neon-text-emerald' },
    degraded: { label: 'Degraded - Active Threats', color: 'text-yellow-400', dot: 'bg-yellow-400', glow: '' },
    critical: { label: 'Critical - Immediate Action', color: 'text-red-400', dot: 'bg-red-400', glow: 'neon-text-red' },
  }[systemStatus];

  const selectedManifest = manifest.find((m) => m.id === selectedHabitation);

  return (
    <div className="min-h-screen data-grid-bg">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-white/5 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 neon-border-cyan">
              <ShieldCheck className="h-6 w-6 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-foreground sm:text-xl">
                Disaster DSS <span className="text-cyan-400">—</span> Role C Dashboard
              </h1>
              <p className="text-xs text-muted-foreground">Decision Support System · Resource Authorization</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden items-center gap-2.5 rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2 sm:flex">
              <span className={cn('h-2 w-2 rounded-full animate-pulse-slow', statusInfo.dot)} />
              <span className={cn('text-xs font-semibold', statusInfo.color, statusInfo.glow)}>{statusInfo.label}</span>
            </div>
            <div className="hidden items-center gap-2 text-xs text-muted-foreground md:flex">
              <Clock className="h-3.5 w-3.5" />
              <span className="font-mono tabular-nums">{currentTime}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">
        {/* Status Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={<Activity className="h-5 w-5" />}
            label="Total Habitations"
            value={loading ? '—' : totalHabitations.toString()}
            subtext="Monitored zones"
            accent="cyan"
          />
          <StatCard
            icon={<AlertTriangle className="h-5 w-5" />}
            label="High Risk Count"
            value={loading ? '—' : highRiskCount.toString()}
            subtext="Critical + High priority"
            accent="red"
          />
          <StatCard
            icon={<Clock className="h-5 w-5" />}
            label="Average TTI"
            value={loading ? '—' : `${avgTTI.toFixed(1)}h`}
            subtext="Time to impact"
            accent="yellow"
          />
          <StatCard
            icon={<Users className="h-5 w-5" />}
            label="Affected Population"
            value={loading ? '—' : totalPopulation.toLocaleString()}
            subtext="Across all zones"
            accent="emerald"
          />
        </div>

        {/* Section 1: Triage Table */}
        <section className="mt-8 animate-slide-up">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10 neon-border-cyan">
                  <TrendingUp className="h-4 w-4 text-cyan-400" />
                </div>
                <h2 className="text-xl font-bold tracking-tight">Habitation Triage List</h2>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">Prioritized by RTS score · Real-time assessment</p>
            </div>
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search habitations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="border-white/10 bg-white/[0.03] pl-9 placeholder:text-muted-foreground/60 focus-visible:border-cyan-500/40"
              />
            </div>
          </div>

          <Card className="glass-card overflow-hidden">
            <ScrollArea className="h-[460px]">
            <Table>
              <TableHeader className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm">
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="w-[70px] text-xs font-semibold uppercase tracking-wider text-muted-foreground">Rank</TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Habitation</TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">RTS Score</TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">TTI (hrs)</TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">SVI</TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">GPS Coordinates</TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i} className="border-white/5">
                      <TableCell colSpan={7}>
                        <div className="h-8 w-full animate-pulse rounded bg-white/5" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  filteredTriage.map((entry) => {
                    const cfg = statusConfig[entry.status];
                    return (
                      <TableRow
                        key={entry.id}
                        className={cn(
                          'group border-white/5 transition-all hover:bg-white/[0.03]',
                          entry.rank <= 2 && 'bg-red-500/[0.02]'
                        )}
                      >
                        <TableCell>
                          <div
                            className={cn(
                              'flex h-9 w-9 items-center justify-center rounded-lg border text-sm font-bold',
                              getRankBadgeClass(entry.rank),
                              getRankGlow(entry.rank)
                            )}
                          >
                            {entry.rank}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="font-medium text-foreground">{entry.habitationName}</div>
                          <div className="text-xs text-muted-foreground">{entry.id} · Pop. {entry.population.toLocaleString()}</div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm font-semibold tabular-nums text-foreground">{entry.rtsScore.toFixed(1)}</span>
                            <div className="hidden w-16 sm:block">
                              <Progress
                                value={entry.rtsScore}
                                className={cn('h-1.5', entry.rtsScore >= 85 ? '[&>*]:bg-red-500' : entry.rtsScore >= 65 ? '[&>*]:bg-yellow-500' : '[&>*]:bg-emerald-500')}
                              />
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className={cn(
                            'font-mono text-sm font-semibold tabular-nums',
                            entry.ttiHours < 4 ? 'text-red-400' : entry.ttiHours < 8 ? 'text-yellow-400' : 'text-emerald-400'
                          )}>
                            {entry.ttiHours.toFixed(1)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="font-mono text-sm tabular-nums text-muted-foreground">{entry.svi.toFixed(1)}</span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <MapPin className="h-3 w-3 text-cyan-400/60" />
                            <span className="font-mono">{entry.gpsLat.toFixed(4)}°, {entry.gpsLng.toFixed(4)}°</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={cn('border font-semibold', cfg.badge)}>
                            <span className={cn('mr-1.5 h-1.5 w-1.5 rounded-full', cfg.dot)} />
                            {cfg.label}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
            </ScrollArea>
          </Card>
        </section>

        {/* Section 2: Authorize Manifest */}
        <section className="mt-8 animate-slide-up">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 neon-border-emerald">
              <Zap className="h-4 w-4 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight">Authorize Manifest</h2>
              <p className="text-sm text-muted-foreground">Issue resource authorization for priority zones</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Action Card */}
            <Card className="glass-card glass-card-hover lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <ShieldCheck className="h-5 w-5 text-cyan-400" />
                  Manifest Authorization
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Select Habitation
                  </label>
                  <Select value={selectedHabitation} onValueChange={setSelectedHabitation}>
                    <SelectTrigger className="border-white/10 bg-white/[0.03] focus:ring-cyan-500/30">
                      <SelectValue placeholder="Choose a habitation to authorize..." />
                    </SelectTrigger>
                    <SelectContent className="border-white/10 bg-popover/95 backdrop-blur-xl">
                      {manifest.map((m) => (
                        <SelectItem key={m.id} value={m.id} disabled={m.authorized}>
                          <div className="flex items-center gap-2">
                            <span className={cn('h-1.5 w-1.5 rounded-full', statusConfig[m.status].dot)} />
                            <span>{m.habitationName}</span>
                            {m.authorized && <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Authorized By Name
                  </label>
                  <Input
                    placeholder="Enter authorizing officer name..."
                    value={authorizedBy}
                    onChange={(e) => setAuthorizedBy(e.target.value)}
                    className="border-white/10 bg-white/[0.03] placeholder:text-muted-foreground/60 focus-visible:border-cyan-500/40"
                  />
                </div>

                {authResult && (
                  <div
                    className={cn(
                      'flex items-center gap-2 rounded-lg border px-4 py-3 text-sm animate-fade-in',
                      authResult.success
                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                        : 'border-red-500/30 bg-red-500/10 text-red-300'
                    )}
                  >
                    {authResult.success ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                    )}
                    <span>{authResult.message}</span>
                  </div>
                )}

                <Button
                  onClick={handleAuthorize}
                  disabled={!selectedHabitation || !authorizedBy.trim() || authorizing}
                  className="glow-button w-full border-0 text-base font-semibold text-white disabled:opacity-40"
                  size="lg"
                >
                  {authorizing ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Authorizing...
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="mr-2 h-5 w-5" />
                      Authorize Manifest
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Resource Preview */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base font-semibold">
                  <Radio className="h-5 w-5 text-emerald-400" />
                  Resource Allocation
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedManifest ? (
                  <div className="space-y-4 animate-fade-in">
                    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
                      <div className="text-xs text-muted-foreground">Selected Zone</div>
                      <div className="mt-1 font-semibold text-foreground">{selectedManifest.habitationName}</div>
                      <div className="mt-1 flex items-center gap-2">
                        <Badge variant="outline" className={cn('border text-xs', statusConfig[selectedManifest.status].badge)}>
                          Rank {selectedManifest.rank} · {statusConfig[selectedManifest.status].label}
                        </Badge>
                      </div>
                    </div>
                    <Separator className="bg-white/5" />
                    <div className="grid grid-cols-2 gap-3">
                      <ResourceItem label="Medical Kits" value={selectedManifest.resourcesAllocated.medical} icon="medical" />
                      <ResourceItem label="Food Units" value={selectedManifest.resourcesAllocated.food} icon="food" />
                      <ResourceItem label="Water (L)" value={selectedManifest.resourcesAllocated.water} icon="water" />
                      <ResourceItem label="Shelter Units" value={selectedManifest.resourcesAllocated.shelter} icon="shelter" />
                    </div>
                    {selectedManifest.authorized && (
                      <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Authorized by {selectedManifest.authorizedBy}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex h-full min-h-[200px] flex-col items-center justify-center text-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/[0.03]">
                      <ChevronRight className="h-6 w-6 text-muted-foreground/50" />
                    </div>
                    <p className="mt-3 text-sm text-muted-foreground">Select a habitation to view allocated resources</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Authorized Manifests Log */}
        {manifest.some((m) => m.authorized) && (
          <section className="mt-8 animate-slide-up">
            <div className="mb-4 flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              <h2 className="text-lg font-bold tracking-tight">Recently Authorized</h2>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {manifest.filter((m) => m.authorized).map((m) => (
                <div key={m.id} className="glass-card glass-card-hover flex items-center justify-between p-4">
                  <div>
                    <div className="font-medium text-foreground">{m.habitationName}</div>
                    <div className="text-xs text-muted-foreground">By {m.authorizedBy}</div>
                  </div>
                  <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-300">
                    <CheckCircle2 className="mr-1.5 h-3 w-3" />
                    Authorized
                  </Badge>
                </div>
              ))}
            </div>
          </section>
        )}

        <footer className="mt-12 border-t border-white/5 pt-6 pb-4 text-center">
          <p className="text-xs text-muted-foreground">
            Disaster DSS · Role C Dashboard · Data refreshes every 30 seconds
          </p>
        </footer>
      </main>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  subtext,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext: string;
  accent: 'cyan' | 'red' | 'yellow' | 'emerald';
}) {
  const accentMap = {
    cyan: { iconBg: 'bg-cyan-500/10', iconColor: 'text-cyan-400', border: 'neon-border-cyan' },
    red: { iconBg: 'bg-red-500/10', iconColor: 'text-red-400', border: 'neon-border-red' },
    yellow: { iconBg: 'bg-yellow-500/10', iconColor: 'text-yellow-400', border: '' },
    emerald: { iconBg: 'bg-emerald-500/10', iconColor: 'text-emerald-400', border: 'neon-border-emerald' },
  }[accent];

  return (
    <Card className={cn('glass-card glass-card-hover p-5', accentMap.border)}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold tabular-nums text-foreground">{value}</p>
          <p className="text-xs text-muted-foreground/70">{subtext}</p>
        </div>
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg', accentMap.iconBg)}>
          <span className={accentMap.iconColor}>{icon}</span>
        </div>
      </div>
    </Card>
  );
}

function ResourceItem({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: 'medical' | 'food' | 'water' | 'shelter';
}) {
  const icons = {
    medical: <Activity className="h-4 w-4 text-cyan-400" />,
    food: <Users className="h-4 w-4 text-emerald-400" />,
    water: <Radio className="h-4 w-4 text-cyan-400" />,
    shelter: <ShieldCheck className="h-4 w-4 text-emerald-400" />,
  }[icon];

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
      <div className="flex items-center gap-2">
        {icons}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <p className="mt-1.5 text-lg font-bold tabular-nums text-foreground">{value}</p>
    </div>
  );
}
