import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { overviewApi, type OverviewResponse } from '../api';
import MetricCard from '../components/MetricCard';
import EmptyState from '../components/EmptyState';
import { formatDate, formatInstruction, formatPercent, truncate } from '../utils/format';

export default function DashboardPage() {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const overview = await overviewApi.getOverview();
        if (!cancelled) {
          setData(overview);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load overview');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <div className="p-6 text-sm text-muted">正在加载仪表盘…</div>;
  }

  if (error || !data) {
    return <div className="p-6 text-sm text-danger">{error ?? '仪表盘不可用'}</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold font-serif">仪表盘</h1>
      <section className="metrics-row">
        <MetricCard label="技能总数" value={data.skills.summary.total_skills_all} hint={`活跃: ${data.skills.summary.total_skills}`} />
        <MetricCard label="平均技能评分" value={data.skills.average_score.toFixed(1)} hint="主要指标 = 有效率 × 100" />
        <MetricCard label="工作流会话" value={data.workflows.total} hint={`记录于 ${data.health.db_path.includes('.openspace') ? '本地仓库' : '工作空间'}`} />
        <MetricCard label="工作流成功率" value={`${data.workflows.average_success_rate.toFixed(1)}%`} hint="平均会话成功率" />
      </section>

      <section>
        <div className="panel-surface p-5 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-muted">健康状态</div>
            <h2 className="text-2xl font-bold font-serif mt-1">运行时快照</h2>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between"><span className="text-muted">状态</span><span>{data.health.status}</span></div>
            <div className="flex items-center justify-between"><span className="text-muted">数据库路径</span><span className="text-right break-all">{data.health.db_path}</span></div>
            <div className="flex items-center justify-between"><span className="text-muted">工作流数量</span><span>{data.health.workflow_count}</span></div>
            <div className="flex items-center justify-between"><span className="text-muted">前端已构建</span><span>{data.health.frontend_dist_exists ? '是' : '否'}</span></div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-6">
        <div className="panel-surface p-5 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-muted">技能</div>
            <h2 className="text-2xl font-bold font-serif mt-1">评分最高的技能</h2>
          </div>
          {data.skills.top.length === 0 ? (
            <EmptyState title="暂无技能" description="请先运行 OpenSpace 任务或将技能同步到本地注册表。" />
          ) : (
            <div className="space-y-3">
              {data.skills.top.map((skill) => (
                <Link key={skill.skill_id} to={`/skills/${encodeURIComponent(skill.skill_id)}`} className="record-card block p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 space-y-1">
                      <div className="font-bold truncate">{skill.name}</div>
                      <div className="text-sm text-muted">{truncate(skill.description || '暂无描述', 110)}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-2xl font-bold font-serif">{skill.score.toFixed(1)}</div>
                      <div className="text-xs text-muted">评分</div>
                    </div>
                  </div>
                  <div className="mt-3 flex gap-3 text-xs text-muted">
                    <span>有效率 {formatPercent(skill.effective_rate)}</span>
                    <span>应用率 {formatPercent(skill.applied_rate)}</span>
                    <span>选择次数 {skill.total_selections}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="panel-surface p-5 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.16em] text-muted">工作流</div>
            <h2 className="text-2xl font-bold font-serif mt-1">最近会话</h2>
          </div>
          {data.workflows.recent.length === 0 ? (
            <EmptyState title="暂无工作流会话" description="启用录制后执行任务，记录将在此显示。" />
          ) : (
            <div className="space-y-3">
              {data.workflows.recent.map((workflow) => (
                <Link key={workflow.id} to={`/workflows/${encodeURIComponent(workflow.id)}`} className="record-card block p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 space-y-1">
                      <div className="font-bold truncate">{workflow.task_name}</div>
                      <div className="text-sm text-muted line-clamp-2">{formatInstruction(workflow.instruction, 160)}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-lg font-bold font-serif">{(workflow.success_rate * 100).toFixed(1)}%</div>
                      <div className="text-xs text-muted">成功率</div>
                    </div>
                  </div>
                  <div className="mt-3 flex gap-3 text-xs text-muted">
                    <span>{workflow.total_steps} 步</span>
                    <span>{workflow.agent_action_count} 智能体动作</span>
                    <span>{formatDate(workflow.start_time)}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
