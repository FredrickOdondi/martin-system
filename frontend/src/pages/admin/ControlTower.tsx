import ConflictDashboard from '../../components/admin/ConflictDashboard';
import GlobalStateDashboard from '../../components/admin/GlobalStateDashboard';

/**
 * Admin Control Tower Page
 * 
 * A standalone page for the Secretariat to manage:
 * - Weekly Packet preparation
 * - Conflict detection and resolution
 * - Force reconciliation
 * - Auto-negotiation between agents
 */
export default function ControlTower() {
    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-2xl text-red-500">radar</span>
                </div>
                <div>
                    <h1 className="text-2xl font-display font-bold text-slate-900 dark:text-white">Control Tower</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Synthesis & Conflict Resolution Center</p>
                </div>
            </div>

            {/* Global State Dashboard */}
            <GlobalStateDashboard />

            {/* Conflict Dashboard Component */}
            <ConflictDashboard />
        </div>
    );
}
