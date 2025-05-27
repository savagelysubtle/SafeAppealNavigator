import json
import os
import shutil


def ensure_dir_exists(file_path_or_dir_path):
    """Ensures the parent directory for a given file path or directory path exists."""
    parent_dir = os.path.dirname(file_path_or_dir_path)
    if parent_dir and not os.path.exists(
        parent_dir
    ):  # Ensure parent_dir is not empty and doesn't exist
        os.makedirs(parent_dir, exist_ok=True)
        print(f"Created directory: {parent_dir}")


def execute_operations(config_path="move.json"):
    """
    Executes file and directory operations based on the provided JSON configuration file.
    Assumes the script is run from the directory where the new project structure
    (e.g., 'AiResearchAgent') should be created.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{config_path}': {e}")
        return

    source_root = config_data.get("source_root")
    if not source_root:
        print("Error: 'source_root' not found in configuration.")
        return

    operations = config_data.get("operations", [])
    if not operations:
        print("No operations found in configuration.")
        return

    print(f"Starting execution of {len(operations)} operations from '{config_path}'...")

    for op_idx, op in enumerate(operations):
        action = op.get("action")
        is_optional = op.get("optional", False)

        print(
            f"\nProcessing operation {op_idx + 1}/{len(operations)}: Action='{action}', Optional={is_optional}"
        )
        # print(f"Details: {op}") # Verbose, uncomment if needed

        if not action:
            print("Skipping operation: 'action' not specified.")
            continue

        try:
            if action == "create_dir":
                target_dir_path = op.get("path")
                if not target_dir_path:
                    print("Skipping create_dir: 'path' not specified.")
                    continue
                os.makedirs(target_dir_path, exist_ok=True)
                print(f"Ensured directory exists: {target_dir_path}")

            elif action == "move_file":
                source_path_orig = op.get("source")
                target_path = op.get("target")

                if not source_path_orig or not target_path:
                    print("Skipping move_file: 'source' or 'target' not specified.")
                    continue

                source_path = (
                    source_path_orig
                    if os.path.isabs(source_path_orig)
                    else os.path.join(source_root, source_path_orig)
                )

                if not os.path.exists(source_path):
                    if is_optional:
                        print(
                            f"Info: Optional source file '{source_path}' not found, skipping move."
                        )
                    else:
                        print(
                            f"Error: Source file '{source_path}' not found (and not optional)."
                        )
                    continue

                ensure_dir_exists(target_path)

                if "content_update_placeholder" in op:
                    content_template = op["content_update_placeholder"]
                    with open(source_path, "r", encoding="utf-8") as sf:
                        original_content = sf.read()

                    new_content = content_template.replace(
                        "{ORIGINAL_CONTENT}", original_content
                    )

                    with open(target_path, "w", encoding="utf-8") as tf:
                        tf.write(new_content)

                    os.remove(source_path)
                    print(
                        f"Processed (moved and content updated): '{source_path}' to '{target_path}'"
                    )
                else:
                    shutil.move(source_path, target_path)
                    print(f"Moved file: '{source_path}' to '{target_path}'")

            elif action == "create_file":
                target_file_path = op.get("path")
                content = op.get("content", "")
                if not target_file_path:
                    print("Skipping create_file: 'path' not specified.")
                    continue

                ensure_dir_exists(target_file_path)
                with open(target_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Created file: '{target_file_path}'")

            elif action == "delete_file":
                file_to_delete_path = op.get("path")
                if not file_to_delete_path:
                    print("Skipping delete_file: 'path' not specified.")
                    continue

                if os.path.exists(file_to_delete_path):
                    os.remove(file_to_delete_path)
                    print(f"Deleted file: '{file_to_delete_path}'")
                elif not is_optional:
                    print(
                        f"Warning: File '{file_to_delete_path}' not found for deletion (and not optional)."
                    )
                else:
                    print(
                        f"Info: Optional file '{file_to_delete_path}' not found, skipping deletion."
                    )

            elif action == "rename_dir":
                source_dir_orig = op.get("source")
                target_dir_path = op.get("target")

                if not source_dir_orig or not target_dir_path:
                    print("Skipping rename_dir: 'source' or 'target' not specified.")
                    continue

                source_dir = (
                    source_dir_orig
                    if os.path.isabs(source_dir_orig)
                    else os.path.join(source_root, source_dir_orig)
                )

                if not (os.path.exists(source_dir) and os.path.isdir(source_dir)):
                    if is_optional:
                        print(
                            f"Info: Optional source directory '{source_dir}' not found or not a directory, skipping rename."
                        )
                    else:
                        print(
                            f"Error: Source directory '{source_dir}' not found or not a directory (and not optional)."
                        )
                    continue

                ensure_dir_exists(target_dir_path)
                shutil.move(source_dir, target_dir_path)
                print(f"Renamed/Moved directory: '{source_dir}' to '{target_dir_path}'")

            elif action == "delete_dir":
                dir_to_delete_path = op.get("path")
                if not dir_to_delete_path:
                    print("Skipping delete_dir: 'path' not specified.")
                    continue

                if os.path.exists(dir_to_delete_path) and os.path.isdir(
                    dir_to_delete_path
                ):
                    shutil.rmtree(dir_to_delete_path)
                    print(f"Deleted directory: '{dir_to_delete_path}'")
                elif not os.path.exists(dir_to_delete_path) and is_optional:
                    print(
                        f"Info: Optional directory '{dir_to_delete_path}' not found, skipping deletion."
                    )
                elif not os.path.exists(dir_to_delete_path) and not is_optional:
                    print(
                        f"Warning: Directory '{dir_to_delete_path}' not found for deletion (and not optional)."
                    )
                elif os.path.exists(dir_to_delete_path) and not os.path.isdir(
                    dir_to_delete_path
                ):
                    print(
                        f"Error: Path '{dir_to_delete_path}' exists but is not a directory. Cannot delete."
                    )
            else:
                print(f"Unknown action: '{action}'. Skipping operation.")

        except Exception as e:
            print(f"Critical error during operation {op_idx + 1} ({action}): {e}")
            if not is_optional:
                print("Stopping execution due to critical error in non-optional step.")
                # return # Uncomment to stop on first critical error in non-optional step

    print("\nAll operations processed.")


if __name__ == "__main__":
    # Assumes 'move.json' is in the same directory as 'move.py' when run.
    execute_operations(config_path="move.json")
