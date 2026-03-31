import { useLayoutEffect, useMemo, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import type { SkillDetail } from '../../api';
import { parseDiff } from '../../utils/diffParser';
import EmptyState from '../EmptyState';
import ProgressBar from '../ProgressBar';
import DiffViewer from './DiffViewer';
import { formatDate, formatPercent, truncate } from '../../utils/format';

interface SkillVersionDrawerProps {
  skill: SkillDetail | null;
  isOpen: boolean;
  onClose: () => void;
}

const DRAWER_ANIMATION_DURATION_MS = 300;
const MAX_RENDERABLE_DIFF_LENGTH = 250_000;
const APP_ROOT_SELECTOR = '#root';
const SKILL_MD_FILENAME = 'SKILL.md';

function resolveSourcePreview(skill: SkillDetail) {
  const snapshot = skill.lineage.content_snapshot;
  if (snapshot && Object.prototype.hasOwnProperty.call(snapshot, SKILL_MD_FILENAME)) {
    return {
      path: `Version snapshot - ${SKILL_MD_FILENAME}`,
      content: snapshot[SKILL_MD_FILENAME] ?? '',
    };
  }

  if (skill.source?.exists && skill.source.content !== null) {
    return {
      path: skill.source.path || skill.path || SKILL_MD_FILENAME,
      content: skill.source.content,
    };
  }

  return null;
}

function lockScroll() {
  const html = document.documentElement;
  const body = document.body;
  const appRoot = document.querySelector<HTMLElement>(APP_ROOT_SELECTOR);
  const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  const supportsStableScrollbarGutter = typeof CSS !== 'undefined' && CSS.supports?.('scrollbar-gutter: stable');

  const bodyScrollbarWidth = supportsStableScrollbarGutter ? 0 : Math.max(0, window.innerWidth - html.clientWidth);

  html.classList.add('drawer-open');
  body.classList.add('drawer-open');
  if (appRoot) {
    appRoot.inert = true;
    appRoot.setAttribute('aria-hidden', 'true');
  }
  if (bodyScrollbarWidth > 0) {
    body.style.paddingRight = `${bodyScrollbarWidth}px`;
  }

  return () => {
    html.classList.remove('drawer-open');
    body.classList.remove('drawer-open');
    body.style.removeProperty('padding-right');
    if (appRoot) {
      appRoot.inert = false;
      appRoot.removeAttribute('aria-hidden');
    }
    if (previouslyFocused && previouslyFocused !== body && previouslyFocused.isConnected) {
      previouslyFocused.focus({ preventScroll: true });
    }
  };
}

export default function SkillVersionDrawer({ skill, isOpen, onClose }: SkillVersionDrawerProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const rawDiff = skill?.lineage.content_diff ?? '';
  const isOversizedDiff = rawDiff.length > MAX_RENDERABLE_DIFF_LENGTH;
  const diffFiles = useMemo(() => (isOversizedDiff ? [] : parseDiff(rawDiff)), [isOversizedDiff, rawDiff]);
  const canShowDiff = rawDiff.trim().length > 0;

  useLayoutEffect(() => {
    if (!skill) {
      return;
    }
    return lockScroll();
  }, [skill]);

  useLayoutEffect(() => {
    if (!isOpen) {
      return;
    }
    closeButtonRef.current?.focus();
  }, [isOpen]);

  useLayoutEffect(() => {
    if (!skill) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, skill]);

  if (!skill) {
    return null;
  }

  const sourcePreview = resolveSourcePreview(skill);

  const drawerContent = (
    <>
      <button
        type="button"
        aria-label="关闭版本详情"
        className={`fixed inset-0 z-30 bg-[rgba(20,20,19,0.22)] transition-opacity duration-300 ${isOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'}`}
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="skill-version-drawer-title"
        className={`fixed top-0 right-0 z-40 flex h-full min-w-[28rem] max-w-[65vw] border-l-2 border-[color:var(--color-ink)] bg-[color:var(--color-surface)] shadow-lg will-change-transform ${isOpen ? 'pointer-events-auto' : 'pointer-events-none'}`}
        style={{
          width: '65vw',
          animation: `${isOpen ? 'drawer-slide-in' : 'drawer-slide-out'} ${DRAWER_ANIMATION_DURATION_MS}ms ease-in-out forwards`,
        }}
      >
        <div className="drawer-scroll flex h-full w-full flex-col overflow-hidden overscroll-contain">
          <header className="p-4 border-b-2 border-[color:var(--color-border)] flex items-start justify-between gap-3 shrink-0">
            <div className="min-w-0">
              <p className="text-xs uppercase tracking-wide text-muted">技能版本</p>
              <h2 id="skill-version-drawer-title" className="font-bold text-lg truncate">{skill.name}</h2>
              <p className="text-xs text-muted font-mono break-all">{skill.skill_id}</p>
            </div>
            <div className="flex items-center gap-2">
              <Link to={`/skills/${encodeURIComponent(skill.skill_id)}`} className="btn-outline-ink text-sm">
                作为主页面打开
              </Link>
              <button type="button" onClick={onClose} ref={closeButtonRef} className="btn-outline-ink text-sm">
                关闭
              </button>
            </div>
          </header>

          <main className="drawer-scroll drawer-scroll-region flex-1 overflow-y-auto overscroll-contain space-y-4 bg-bg-page p-4">
            <section className="rounded-[var(--radius)] border-2 border-[color:var(--color-border-dark)] bg-surface p-4 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2 min-w-0">
                  <div className="text-xs uppercase tracking-[0.16em] text-muted">版本摘要</div>
                  <div className="text-sm text-muted">{skill.description || '此版本暂无描述。'}</div>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="tag px-2 py-1">{skill.category}</span>
                    <span className="tag px-2 py-1">{skill.origin}</span>
                    <span className="tag px-2 py-1">代数 {skill.generation}</span>
                    <span className="tag px-2 py-1">{skill.is_active ? '活跃' : '非活跃'}</span>
                    {skill.tags.map((tag) => (
                      <span key={tag} className="tag px-2 py-1">{tag}</span>
                    ))}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-4xl font-bold font-serif leading-none">{skill.score.toFixed(1)}</div>
                  <div className="text-xs uppercase tracking-[0.16em] text-muted mt-2">版本评分</div>
                </div>
              </div>
            </section>

            <section className="rounded-[var(--radius)] border-2 border-[color:var(--color-border-dark)] bg-surface p-4 space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.16em] text-muted">指标</div>
                <h3 className="text-xl font-bold font-serif mt-1">执行质量</h3>
              </div>
              <div className="space-y-4">
                <ProgressBar label="有效率" value={skill.effective_rate} colorClass="bg-primary" />
                <ProgressBar label="完成率" value={skill.completion_rate} colorClass="bg-accent" />
                <ProgressBar label="应用率" value={skill.applied_rate} colorClass="bg-teal" />
                <ProgressBar label="回退率" value={skill.fallback_rate} colorClass="bg-danger" />
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm text-muted">
                <div><div className="font-bold text-ink">选择次数</div><div>{skill.total_selections}</div></div>
                <div><div className="font-bold text-ink">应用次数</div><div>{skill.total_applied}</div></div>
                <div><div className="font-bold text-ink">完成次数</div><div>{skill.total_completions}</div></div>
                <div><div className="font-bold text-ink">回退次数</div><div>{skill.total_fallbacks}</div></div>
              </div>
            </section>

            <section className="rounded-[var(--radius)] border-2 border-[color:var(--color-border-dark)] bg-surface p-4 text-sm space-y-2">
              <h3 className="font-bold">版本元数据</h3>
              <p><strong>来源:</strong> {skill.origin}</p>
              <p><strong>代数:</strong> {skill.generation}</p>
              <p><strong>可见性:</strong> {skill.visibility}</p>
              <p><strong>创建时间:</strong> {formatDate(skill.lineage.created_at)}</p>
              <p><strong>首次发现:</strong> {formatDate(skill.first_seen)}</p>
              <p><strong>最后更新:</strong> {formatDate(skill.last_updated)}</p>
              <p><strong>技能路径:</strong> <span className="break-all">{skill.path || '不可用'}</span></p>
              <p><strong>技能目录:</strong> <span className="break-all">{skill.skill_dir || '不可用'}</span></p>
              <p><strong>父技能ID:</strong> {skill.parent_skill_ids.length ? skill.parent_skill_ids.join(', ') : '无'}</p>
              <p><strong>变更摘要:</strong> {skill.lineage.change_summary || '无'}</p>
              <p><strong>有效评分:</strong> {formatPercent(skill.effective_rate)}</p>
            </section>

            <section className="rounded-[var(--radius)] border-2 border-[color:var(--color-border-dark)] bg-surface p-4 space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.16em] text-muted">差异</div>
                <h3 className="text-xl font-bold font-serif mt-1">内容差异</h3>
              </div>
              {isOversizedDiff ? (
                <EmptyState title="差异过大" description="此版本的内容差异非常大，因此内联查看器已禁用。" />
              ) : canShowDiff ? (
                diffFiles.length > 0 ? (
                  <DiffViewer files={diffFiles} />
                ) : (
                  <EmptyState title="差异不可用" description="此版本有差异数据，但无法解析为统一差异格式。" />
                )
              ) : (
                <EmptyState title="无内容差异" description="此版本没有存储的内容差异。" />
              )}
            </section>

            <section className="rounded-[var(--radius)] border-2 border-[color:var(--color-border-dark)] bg-surface p-4 space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.16em] text-muted">源文件</div>
                <h3 className="text-xl font-bold font-serif mt-1">SKILL.md 预览</h3>
              </div>
              {sourcePreview ? (
                <div className="space-y-3">
                  <div className="text-xs text-muted break-all">{sourcePreview.path}</div>
                  <pre className="field-surface p-4 text-xs overflow-auto max-h-[320px] whitespace-pre-wrap">{sourcePreview.content}</pre>
                </div>
              ) : (
                <EmptyState title="源文件不可用" description="此版本指向一个缺失或无法读取的 SKILL.md 路径。" />
              )}
            </section>

            <section className="rounded-[var(--radius)] border-2 border-[color:var(--color-border-dark)] bg-surface p-4 space-y-4">
              <div>
                <div className="text-xs uppercase tracking-[0.16em] text-muted">分析</div>
                <h3 className="text-xl font-bold font-serif mt-1">最近执行分析</h3>
              </div>
              {skill.recent_analyses.length > 0 ? (
                <div className="space-y-3">
                  {skill.recent_analyses.map((analysis) => (
                    <div key={`${analysis.task_id}-${analysis.timestamp}`} className="panel-subtle p-4 bg-surface space-y-2">
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-bold truncate">{analysis.task_id}</div>
                        <div className="text-xs text-muted">{formatDate(analysis.timestamp)}</div>
                      </div>
                      <div className="text-sm text-muted">{truncate(analysis.execution_note || '无执行备注', 220)}</div>
                      <div className="text-xs text-muted">
                        已完成: {analysis.task_completed ? '是' : '否'} · 工具问题: {analysis.tool_issues.length} · 建议: {analysis.evolution_suggestions.length}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="暂无分析" description="执行分析将在任务运行记录持久化到 SQLite 后出现。" />
              )}
            </section>
          </main>
        </div>
      </aside>
    </>
  );

  if (typeof document === 'undefined') {
    return drawerContent;
  }

  return createPortal(drawerContent, document.body);
}
