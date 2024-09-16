import os
import logging

logger = logging.getLogger(__name__)

def get_repository_items():
    repo_items = {}
    material_repo = "material_repo"
    logger.info(f"Scanning directory: {material_repo}")
    
    if not os.path.exists(material_repo):
        logger.warning(f"Directory {material_repo} does not exist")
        return repo_items

    for category in os.listdir(material_repo):
        category_path = os.path.join(material_repo, category)
        if os.path.isdir(category_path):
            components = []
            for component in os.listdir(category_path):
                if component.endswith('.html'):
                    component_id = f"{category}-{component.replace('.html', '')}"
                    components.append({"id": component_id, "name": component.replace('.html', '')})
            if components:
                repo_items[category] = components
    
    logger.info(f"Repository items found: {repo_items}")
    return repo_items