from .models import BinaryNode


def _profile_picture_url(user, request=None):
    if user.profile_picture:
        url = user.profile_picture.url
        return request.build_absolute_uri(url) if request else url
    if user.profile_picture_data_url:
        return user.profile_picture_data_url
    return None


def serialize_node(user, request=None):
    children = {node.side: node.user for node in BinaryNode.objects.filter(parent=user)}
    return {
        "id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "position": user.placement_side or "root",
        "profilePicture": _profile_picture_url(user, request=request),
        "leftTeamCount": user.left_team_count,
        "rightTeamCount": user.right_team_count,
        "children": {
            "left": serialize_node(children["left"], request=request) if "left" in children else None,
            "right": serialize_node(children["right"], request=request) if "right" in children else None,
        },
    }


def build_tree_payload(user, request=None):
    node = BinaryNode.objects.filter(user=user).first()
    root_user = user
    while node and node.parent:
        root_user = node.parent
        node = BinaryNode.objects.filter(user=root_user).first()
    return serialize_node(root_user, request=request)


def get_children_map(user):
    return {node.side: node.user for node in BinaryNode.objects.filter(parent=user).select_related("user")}


def find_next_open_slot(root_user, preferred_side):
    if preferred_side not in {"left", "right"}:
        raise ValueError("Preferred side must be left or right.")

    current = root_user
    while True:
        next_branch_node = (
            BinaryNode.objects.filter(parent=current, side=preferred_side)
            .select_related("user")
            .first()
        )
        if not next_branch_node:
            return current, preferred_side
        current = next_branch_node.user
