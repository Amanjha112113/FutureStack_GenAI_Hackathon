from pathlib import Path

def load_context():
    """Load all files from context directory"""
    # Use __file__ to get the path relative to this script
    context_dir = Path(__file__).parent / "context"
    all_content = ""
    for file_path in context_dir.glob("*"):
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8')
                all_content += f"\n=== {file_path.name} ===\n{content}\n"
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                pass
    return all_content.strip() or "No context files found"