
class ModelMapper():
    def to_workspace_list(workspace_models):
        workspaceList = []
        for workspace in workspace_models:
            workspaceList.append({
                "uuid": workspace["uuid"],
                "name": workspace["name"],
            })

        return workspaceList

    def to_single_workspace(workspace_models):
        workspaceDict = {}
        for workspace in workspace_models:
            workspaceDict["uuid"] = workspace["uuid"]
            workspaceDict["name"] = workspace["name"]

        return workspaceDict
