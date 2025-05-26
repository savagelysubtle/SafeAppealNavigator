"""
Interactive Chat Tab Component

Provides a dedicated chat interface for legal consultation, document analysis,
and AI-powered assistance throughout the research process.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import gradio as gr

from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


class InteractiveChatManager:
    """Manages the state and functionality of the interactive chat system."""

    def __init__(self):
        self.chat_sessions: Dict[str, List[Dict[str, str]]] = {}
        self.active_session_id: Optional[str] = None
        self.context_data: Dict[str, Any] = {}
        self.chat_modes = {
            "general": "General legal consultation and guidance",
            "document": "Document-specific analysis and review",
            "research": "Legal research and precedent finding",
            "strategy": "Case strategy and argument development",
            "workflow": "Workflow and process assistance",
        }

    def create_session(self, session_id: str) -> str:
        """Create a new chat session."""
        self.chat_sessions[session_id] = []
        self.active_session_id = session_id
        logger.info(f"Created new chat session: {session_id}")
        return session_id

    def add_context(self, context_type: str, context_data: Any) -> None:
        """Add context data for the chat to reference."""
        self.context_data[context_type] = context_data
        logger.info(f"Added context type: {context_type}")

    def get_session_history(
        self, session_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Get chat history for a session."""
        sid = session_id or self.active_session_id
        if sid and sid in self.chat_sessions:
            return self.chat_sessions[sid]
        return []


def create_interactive_chat_tab(webui_manager: WebuiManager):
    """Create the standalone Interactive Chat tab for legal consultation."""

    # Initialize chat manager
    chat_manager = InteractiveChatManager()

    # Create initial session
    initial_session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    chat_manager.create_session(initial_session_id)

    tab_components = {}

    with gr.Column():
        # Header
        gr.Markdown("""
        # 💬 Interactive Legal Consultation Chat
        *AI-powered legal assistance, document analysis, and research guidance*

        This intelligent chat system provides comprehensive support throughout your legal research journey.
        Ask questions, analyze documents, develop strategies, and get expert guidance tailored to your case.
        """)

        # Chat Configuration
        with gr.Group():
            gr.Markdown("## 🎯 Chat Configuration")

            with gr.Row():
                with gr.Column(scale=3):
                    chat_mode = gr.Radio(
                        choices=[
                            ("General Consultation", "general"),
                            ("Document Analysis", "document"),
                            ("Legal Research", "research"),
                            ("Strategy Discussion", "strategy"),
                            ("Workflow Assistance", "workflow"),
                        ],
                        value="general",
                        label="💡 Consultation Mode",
                        info="Select the type of assistance you need",
                    )

                with gr.Column(scale=2):
                    context_status = gr.Textbox(
                        label="📋 Context Status",
                        value="No active context loaded",
                        lines=2,
                        interactive=False,
                        info="Shows what documents or workflows are available for reference",
                    )

        # Main Chat Interface
        with gr.Group():
            gr.Markdown("## 💬 Legal Consultation Chat")

            chat_history = gr.Chatbot(
                label="Chat History",
                height=500,
                show_label=False,
                elem_classes="legal-chat-interface",
                avatar_images=(None, "🤖"),
            )

            with gr.Row():
                with gr.Column(scale=5):
                    chat_input = gr.Textbox(
                        label="Your Question",
                        placeholder="Ask about your case, request document analysis, get legal guidance...",
                        lines=3,
                        max_lines=5,
                        interactive=True,
                        show_label=False,
                    )

                with gr.Column(scale=1):
                    with gr.Column():
                        chat_send_btn = gr.Button(
                            "📤 Send",
                            variant="primary",
                            size="lg",
                            elem_classes="chat-send-button",
                        )
                        chat_clear_btn = gr.Button(
                            "🗑️ Clear Chat", variant="secondary", size="sm"
                        )

        # Quick Actions
        with gr.Group():
            gr.Markdown("## ⚡ Quick Actions")

            with gr.Row():
                quick_action_btns = [
                    gr.Button("📄 Analyze Document", variant="secondary"),
                    gr.Button("🔍 Find Precedents", variant="secondary"),
                    gr.Button("📝 Draft Appeal", variant="secondary"),
                    gr.Button("💡 Strategy Tips", variant="secondary"),
                    gr.Button("❓ Explain Process", variant="secondary"),
                ]

        # Context Management
        with gr.Group():
            gr.Markdown("## 📁 Context & Document Management")

            with gr.Row():
                with gr.Column():
                    document_upload = gr.File(
                        label="📎 Upload Documents for Analysis",
                        file_count="multiple",
                        file_types=[".pdf", ".doc", ".docx", ".txt"],
                        interactive=True,
                    )

                    loaded_docs_display = gr.Textbox(
                        label="📚 Loaded Documents",
                        value="No documents loaded",
                        lines=3,
                        interactive=False,
                    )

                with gr.Column():
                    workflow_connection = gr.Dropdown(
                        choices=["No active workflows"],
                        value="No active workflows",
                        label="🔗 Connect to Workflow",
                        info="Link chat to an active workflow for context",
                    )

                    case_info = gr.Textbox(
                        label="📋 Case Information",
                        placeholder="Enter case details for context...",
                        lines=3,
                        interactive=True,
                    )

        # Chat Features
        with gr.Accordion("🎛️ Advanced Chat Features", open=False):
            with gr.Row():
                temperature_slider = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.3,
                    step=0.1,
                    label="🌡️ Response Temperature",
                    info="Lower = more focused, Higher = more creative",
                )

                max_history = gr.Number(
                    label="📜 Max History Length",
                    value=10,
                    minimum=5,
                    maximum=50,
                    info="Number of previous messages to maintain context",
                )

            export_chat_btn = gr.Button("💾 Export Chat History", variant="secondary")

            gr.Markdown("""
            **💡 Advanced Tips:**
            - Upload documents for detailed analysis and cross-referencing
            - Connect to active workflows for contextual assistance
            - Use specific consultation modes for targeted help
            - Export chat history for record-keeping
            """)

    # Store components
    tab_components.update(
        {
            "chat_mode": chat_mode,
            "context_status": context_status,
            "chat_history": chat_history,
            "chat_input": chat_input,
            "chat_send_btn": chat_send_btn,
            "chat_clear_btn": chat_clear_btn,
            "document_upload": document_upload,
            "loaded_docs_display": loaded_docs_display,
            "workflow_connection": workflow_connection,
            "case_info": case_info,
            "temperature_slider": temperature_slider,
            "max_history": max_history,
            "export_chat_btn": export_chat_btn,
        }
    )

    # Add quick action buttons to components
    for i, btn in enumerate(quick_action_btns):
        tab_components[f"quick_action_{i}"] = btn

    webui_manager.add_components("interactive_chat", tab_components)

    # Event Handlers

    async def send_chat_message(
        message: str, history: List, chat_mode_val: str, case_info_val: str
    ):
        """Process and respond to chat messages."""
        try:
            if not message.strip():
                return history, ""

            # Add user message to history
            history.append([message, None])

            # Check if we have global settings for LLM
            if (
                hasattr(webui_manager, "global_settings_manager")
                and webui_manager.global_settings_manager
            ):
                # Simulate AI response (would integrate with actual LLM here)
                mode_context = chat_manager.chat_modes.get(
                    chat_mode_val, "general consultation"
                )

                # Generate contextual response based on mode
                if chat_mode_val == "document":
                    response = f"📄 **Document Analysis Mode**\n\nI'll help you analyze your documents. You asked: '{message}'\n\nTo provide the best analysis, please upload the specific documents you'd like me to review."
                elif chat_mode_val == "research":
                    response = f"🔍 **Legal Research Mode**\n\nI'll help you find relevant precedents and cases. Regarding '{message}':\n\n• Search for similar cases in the database\n• Look for precedents with comparable circumstances\n• Review recent decisions on this topic"
                elif chat_mode_val == "strategy":
                    response = f"💡 **Strategy Discussion Mode**\n\nLet's develop your legal strategy. Based on your question about '{message}':\n\n• Consider the strengths of your position\n• Identify potential challenges\n• Develop supporting arguments"
                elif chat_mode_val == "workflow":
                    response = f"🔄 **Workflow Assistance Mode**\n\nI'll guide you through the process. For '{message}':\n\n• Current workflow status\n• Next recommended steps\n• Required documentation"
                else:
                    response = f"💬 **General Consultation**\n\nI understand you're asking about '{message}'. Let me provide some guidance based on general legal principles and best practices."

                # Add case context if available
                if case_info_val and case_info_val.strip():
                    response += f"\n\n📋 **Case Context**: {case_info_val[:100]}..."

            else:
                response = "⚠️ **Note**: LLM integration pending. This is a demonstration of the chat interface structure."

            # Update history with response
            history[-1][1] = response

            # Store in chat manager
            if chat_manager.active_session_id:
                chat_manager.chat_sessions[chat_manager.active_session_id].append(
                    {
                        "user": message,
                        "assistant": response,
                        "timestamp": datetime.now().isoformat(),
                        "mode": chat_mode_val,
                    }
                )

            return history, ""

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            history.append([message, f"❌ Error: {str(e)}"])
            return history, ""

    def clear_chat_history():
        """Clear the current chat session."""
        if chat_manager.active_session_id:
            chat_manager.chat_sessions[chat_manager.active_session_id] = []
        return []

    def handle_document_upload(files):
        """Handle document uploads for analysis."""
        if not files:
            return "No documents loaded"

        doc_list = []
        for file in files:
            if hasattr(file, "name"):
                doc_name = file.name.split("/")[-1]
                doc_list.append(f"📄 {doc_name}")
                # Add to chat context
                chat_manager.add_context(f"document_{doc_name}", file.name)

        return f"Loaded {len(doc_list)} documents:\n" + "\n".join(doc_list)

    def update_context_status(loaded_docs: str, workflow: str, case_info: str):
        """Update the context status display."""
        status_lines = []

        if loaded_docs and loaded_docs != "No documents loaded":
            doc_count = loaded_docs.count("📄")
            status_lines.append(f"📄 {doc_count} documents loaded")

        if workflow and workflow != "No active workflows":
            status_lines.append(f"🔗 Connected to: {workflow}")

        if case_info and case_info.strip():
            status_lines.append("📋 Case context available")

        if status_lines:
            return "\n".join(status_lines)
        else:
            return "No active context loaded"

    async def handle_quick_action(action_index: int, history: List):
        """Handle quick action button clicks."""
        quick_actions = [
            "Please analyze the uploaded documents and provide a summary",
            "Find legal precedents similar to my case",
            "Help me draft an appeal notice",
            "What strategies would you recommend for my case?",
            "Explain the legal process I need to follow",
        ]

        if action_index < len(quick_actions):
            message = quick_actions[action_index]
            return await send_chat_message(message, history, "general", "")

        return history, ""

    def export_chat_history():
        """Export the current chat session."""
        if chat_manager.active_session_id:
            session_data = chat_manager.chat_sessions[chat_manager.active_session_id]
            # This would export to a file in a real implementation
            return f"💾 Exported {len(session_data)} messages from session {chat_manager.active_session_id}"
        return "No chat history to export"

    # Wire up event handlers
    chat_send_btn.click(
        fn=send_chat_message,
        inputs=[chat_input, chat_history, chat_mode, case_info],
        outputs=[chat_history, chat_input],
    )

    chat_input.submit(
        fn=send_chat_message,
        inputs=[chat_input, chat_history, chat_mode, case_info],
        outputs=[chat_history, chat_input],
    )

    chat_clear_btn.click(
        fn=clear_chat_history,
        outputs=[chat_history],
    )

    document_upload.change(
        fn=handle_document_upload,
        inputs=[document_upload],
        outputs=[loaded_docs_display],
    )

    # Update context status when any context changes
    for context_input in [loaded_docs_display, workflow_connection, case_info]:
        context_input.change(
            fn=update_context_status,
            inputs=[loaded_docs_display, workflow_connection, case_info],
            outputs=[context_status],
        )

    # Connect quick action buttons
    for i, btn in enumerate(quick_action_btns):
        btn.click(
            fn=lambda hist, idx=i: handle_quick_action(idx, hist),
            inputs=[chat_history],
            outputs=[chat_history, chat_input],
        )

    export_chat_btn.click(
        fn=export_chat_history,
        outputs=[context_status],
    )

    # Store chat manager in webui_manager for cross-component access
    webui_manager.chat_manager = chat_manager

    logger.info("✅ Interactive Chat tab initialized successfully")
