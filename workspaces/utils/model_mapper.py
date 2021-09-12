
class ModelMapper():
    def to_workspace_list(workspace_models):
        workspaceList = []
        for workspace in workspace_models:
            workspaceList.append({
                "uuid": workspace["uuid"],
                "name": workspace["name"],
            })

        return workspaceList
