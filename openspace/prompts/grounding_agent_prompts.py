from typing import List, Optional, Set


class GroundingAgentPrompts:
    
    TASK_COMPLETE = "<COMPLETE>"

    @classmethod
    def build_system_prompt(cls, backends: Optional[List[str]] = None) -> str:
        """Build a system prompt tailored to the actually registered backends.

        Args:
            backends: Active backend names (e.g. ``["shell", "mcp", "gui"]``).
                ``None`` falls back to all backends for backward compatibility.
        """
        scope: Set[str] = set(backends) if backends else {"gui", "shell", "mcp", "web", "system"}

        sections: List[str] = []

        # Core
        sections.append(
            "你是一个 Grounding Agent（落地执行智能体）。使用工具执行任务。\n\n"
            "# 工具执行\n\n"
            "- 根据描述和模式选择合适的工具\n"
            "- 提供正确的参数\n"
            "- 如有需要可调用多个工具\n"
            "- 工具立即执行，结果将在下一次迭代中显示\n"
            "- 如果需要结果来决定下一步操作，请等待下一次迭代"
        )

        # Tool Selection Tips (only mention backends that exist)
        tips: List[str] = []
        has_mcp = "mcp" in scope
        has_shell = "shell" in scope
        has_gui = "gui" in scope

        if has_mcp and has_shell:
            tips.append("- **MCP 工具**和**Shell 工具**在适用时通常更快、更准确")
        elif has_mcp:
            tips.append("- **MCP 工具**在适用时通常更快、更准确")
        elif has_shell:
            tips.append("- **Shell 工具**对于命令行和脚本任务快速且准确")

        if has_gui:
            if has_mcp or has_shell:
                tips.append("- **GUI 工具**提供更精细的控制，可以处理其他工具无法覆盖的任务")
            else:
                tips.append("- **GUI 工具**提供与图形界面的直接交互")
            tips.append("- 根据任务需求和工具可用性进行选择")

        if tips:
            sections.append("# 工具选择提示\n\n" + "\n".join(tips))

        # Visual Analysis Control
        if has_gui:
            sections.append(
                "# 视觉分析控制\n\n"
                "GUI 工具会自动分析截图以提取信息。\n\n"
                "当不需要分析时，添加参数跳过：\n"
                "```json\n"
                '{"task_description": "...", "skip_visual_analysis": true}\n'
                "```\n\n"
                "**决策规则：**\n"
                "- 任务目标是操作性的（打开/导航/点击/显示）：跳过分析\n"
                "- 任务目标需要知识提取（读取/提取/保存数据）：保留分析\n\n"
                "**示例：**\n"
                '- "打开设置页面"：仅操作，跳过分析\n'
                '- "打开设置并记录所有值"：需要知识，保留分析\n'
                '- "导航到 GitHub 主页"：仅操作，跳过分析\n'
                '- "搜索 Python 教程并保存前 5 个标题"：需要知识，保留分析\n\n'
                "**关键原则：** 如果你需要从屏幕提取信息用于后续步骤或向用户报告，"
                "保留分析（不跳过）。\n"
                "**注意：** 只有 GUI 工具支持此参数。其他后端工具会忽略它。"
            )

        # Mid-iteration skill retrieval hint
        sections.append(
            "# 技能检索\n\n"
            "如果当前方法失败，或任务需要你缺乏的领域特定知识，"
            "请调用 `retrieve_skill` 并简要描述你需要的指导。"
            "它会返回可用的已验证流程。"
        )

        # Task Completion (always present)
        sections.append(
            "# 任务完成\n\n"
            "每次迭代后，评估任务是否完成：\n\n"
            "**如果任务已完成：**\n"
            "- 写一个总结响应，说明完成了什么\n"
            f"- 在响应末尾新行添加完成标记 `{cls.TASK_COMPLETE}`\n"
            "- 响应格式示例：\n"
            "  ```\n"
            "  我已成功完成任务。文件已创建于 /path/to/file.txt，包含请求的内容。\n"
            f"\n  {cls.TASK_COMPLETE}\n"
            "  ```\n\n"
            "**如果任务未完成：**\n"
            "- 继续调用适当的工具\n"
            f"- 不要输出 `{cls.TASK_COMPLETE}`\n"
            "- 工具结果将在下一次迭代中显示\n\n"
            f"标记 `{cls.TASK_COMPLETE}` 表示不需要进一步迭代。"
        )

        return "\n\n".join(sections)

    @staticmethod
    def iteration_summary(
        instruction: str,
        iteration: int,
        max_iterations: int
    ) -> str:
        """
        Build iteration summary prompt for LLMClient auto-summary.
        LLM extracts information directly from tool results in conversation history.
        """
        return f"""根据原始任务和上述对话中的工具执行结果，生成结构化的迭代摘要。

**原始任务：**
{instruction}

**进度：** 第 {iteration} 次迭代，共 {max_iterations} 次

**按以下格式生成摘要：**

## 第 {iteration} 次迭代进度

执行的操作：<调用了哪些工具，做了什么>

获取的知识（完整且具体）：
- 文件位置：<所有创建/读取/修改的文件路径/名称及确切位置，或"无">
- 视觉内容：<从截图中提取的所有可见信息 - 文本、数据、列表、表格、结果，或"不适用">
- 检索的数据：<从搜索/查询中获得的所有关键数据/结果，包含具体数值、数字、名称，或"不适用">
- URL/链接：<找到的所有重要 URL、链接或标识符，或"不适用">
- 系统状态：<重要的状态变化、错误消息、状态指示器，或"不适用">

遇到的错误：<工具执行中的任何错误或问题，或"无">

关键指南：
- 此摘要用于保存知识供后续迭代使用
- 从上述对话的工具输出中提取所有具体信息
- 文件名、路径、URL - 使用工具输出中的确切值
- 视觉内容 - 提取实际可见的文本/数据，而非仅"看到了什么"
- 搜索结果 - 包含具体数据，而非模糊描述
- 下一次迭代无法看到当前工具输出 - 此摘要是唯一的知识来源"""
    
    @staticmethod
    def visual_analysis(
        tool_name: str,
        num_screenshots: int,
        task_description: str = ""
    ) -> str:
        """
        Build prompt for visual analysis of screenshots.

        Args:
            tool_name: Tool name that generated the screenshots
            num_screenshots: Number of screenshots
            task_description: Original task description for context
        """
        screenshot_text = "截图" if num_screenshots == 1 else f"{num_screenshots} 张截图"
        these_text = "这张截图" if num_screenshots == 1 else "这些截图"

        task_context = f"""
**原始任务**: {task_description}

专注于提取与此任务相关的信息。优先考虑有助于完成任务的内容。
""" if task_description else ""

        return f"""从{these_text}中提取知识和信息。这些内容将传递给下一次迭代，使其能够继续处理这些信息（搜索、分析、保存等）。如果不进行提取，视觉内容将只能被人类查看，无法用于后续操作。
{task_context}
**提取所有可见的知识内容**（优先考虑与任务相关的信息）：
1. **文本内容**：文章、文档、代码、消息、描述 - 提取实际文本
2. **数据点**：数字、统计、测量、数值、百分比 - 要具体
3. **列表项**：名称、标题、列表/搜索结果/文件中的条目 - 列出来
4. **结构化数据**：表格、图表、表单中的信息 - 描述其内容
5. **关键信息**：URL、路径、名称、ID、日期、标签 - 任何对下一步有用的信息

**忽略界面元素**：
- 按钮、菜单、工具栏、导航栏
- UI 设计、布局、颜色、样式
- 非信息性的视觉元素

**目标**：提取可用的知识，使下一个智能体能够以编程方式处理这些信息。要具体且完整，但专注于与任务相关的内容。

来自工具 '{tool_name}' 的{screenshot_text}"""
    
    @staticmethod
    def final_summary(
        instruction: str,
        iterations: int
    ) -> str:
        """
        Build prompt for generating final summary across all iterations.
        """
        return f"""根据上述完整对话历史（包括所有 {iterations} 次迭代摘要和工具执行），生成全面的最终摘要。

## 最终任务摘要

任务：{instruction}

完成情况：<所有迭代中完成的所有操作的全面描述>

获取的关键信息：<发现的所有重要信息>
- 文件：<创建/读取/修改的文件及路径，或"不适用">
- 数据：<获取的重要数据/结果，或"不适用">
- 发现：<关键发现或见解，或"不适用">

遇到的问题：<任何错误或问题，或"无">

结果：<"成功"或"未完成">

指南：
- 整合所有迭代摘要的信息
- 包含具体的交付物（文件路径、数据等）
- 全面但简洁
- 专注于用户关心的内容"""
    
    @staticmethod
    def workspace_directory(workspace_dir: str) -> str:
        """
        Build workspace directory information for cross-iteration/cross-backend data sharing.
        """
        import os
        # Check if this is a benchmark scenario:
        # 1. LiveMCPBench /root mapping
        # 2. Workspace already contains files (e.g. GDPVal reference files)
        is_benchmark = "/root" in workspace_dir or "LiveMCPBench/root" in workspace_dir
        if not is_benchmark:
            try:
                has_existing_files = os.path.isdir(workspace_dir) and bool(os.listdir(workspace_dir))
            except OSError:
                has_existing_files = False
            is_benchmark = has_existing_files

        if is_benchmark:
            # Benchmark / task mode: task files are in workspace directory
            return f"""**工作目录**：`{workspace_dir}`
- 所有任务文件（输入/输出）都位于此目录
- 所有文件操作都应在此目录中读取和写入"""
        else:
            # Normal mode: workspace is for intermediate results
            return f"""**工作目录**：`{workspace_dir}`
- 在此保存中间结果；后续迭代/后端可以读取你之前保存的内容
- 注意：用户的个人文件不在这里 - 请在 ~/Desktop、~/Documents、~/Downloads 等位置搜索"""
    
    @staticmethod
    def workspace_matching_files(matching_files: List[str]) -> str:
        """
        Build alert for files matching task requirements.
        """
        files_str = ', '.join([f"`{f}`" for f in matching_files])
        return f"""**工作目录提醒**：发现匹配任务要求的文件：{files_str}
- 读取这些文件以验证是否满足任务要求
- 如满足，标记任务为已完成
- 如不满足，修改或重新创建"""
    
    @staticmethod
    def workspace_recent_files(total_files: int, recent_files: List[str]) -> str:
        """
        Build info for recently modified files.
        """
        recent_list = ', '.join([f"`{f}`" for f in recent_files[:15]])
        return f"""**工作目录信息**：共 {total_files} 个文件，{len(recent_files)} 个最近修改
最近文件：{recent_list}
创建新文件前请考虑检查最近文件"""
    
    @staticmethod
    def workspace_file_list(files: List[str]) -> str:
        """
        Build list of all existing files.
        """
        files_list = ', '.join([f"`{f}`" for f in files[:15]])
        if len(files) > 15:
            files_list += f"（还有 {len(files) - 15} 个）"
        return f"**工作目录信息**：{len(files)} 个现有文件：{files_list}"
    
    @staticmethod
    def iteration_feedback(
        iteration: int,
        llm_summary: str,
        add_guidance: bool = True
    ) -> str:
        """
        Build feedback message to pass iteration summary to next iteration.
        """
        content = f"""## 第 {iteration} 次迭代摘要

{llm_summary}"""

        if add_guidance:
            content += f"""
---
现在继续第 {iteration + 1} 次迭代。你可以在上方看到完整的对话历史。根据目前的所有进展，决定是否：
- 如果任务尚未完成，调用更多工具
- 如果任务已完全完成，输出 {GroundingAgentPrompts.TASK_COMPLETE}"""

        return content