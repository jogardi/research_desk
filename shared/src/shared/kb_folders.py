from shared.config import Config

def ROOT_FOLDER(kb_name: str) -> str:
    base_root = Config.ROOT_FOLDER
    root_folder = f"{base_root}/{kb_name}" if kb_name else base_root
    print(f"*** ROOT_FOLDER: {root_folder}")
    return root_folder

def DB_FOLDER(kb_name: str) -> str:
    return f"{ROOT_FOLDER(kb_name)}/database"

def KNOWLEDGEBASE_FOLDER(kb_name: str) -> str:
    return f"{ROOT_FOLDER(kb_name)}/knowledgebase"