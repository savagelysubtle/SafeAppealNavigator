import argparse
import logging

from dotenv import load_dotenv

from src.ai_research_assistant.webui.interface import create_ui, theme_map

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

load_dotenv()


def main():
    logger.info("🚀 Starting AI Research Assistant WebUI...")

    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument(
        "--ip", type=str, default="127.0.0.1", help="IP address to bind to"
    )
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument(
        "--theme",
        type=str,
        default="Ocean",
        choices=theme_map.keys(),
        help="Theme to use for the UI",
    )
    args = parser.parse_args()

    logger.info("📋 Configuration:")
    logger.info(f"  - IP: {args.ip}")
    logger.info(f"  - Port: {args.port}")
    logger.info(f"  - Theme: {args.theme}")

    try:
        logger.info("🎨 Creating UI interface...")
        demo = create_ui(theme_name=args.theme)
        logger.info("✅ UI interface created successfully")

        logger.info(f"🌐 Launching server on {args.ip}:{args.port}...")
        demo.queue().launch(
            server_name=args.ip,
            server_port=args.port,
            show_error=True,  # Show detailed error messages
            share=False,
            inbrowser=False,
            quiet=False,
        )
        logger.info("✅ Server launched successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start WebUI: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
