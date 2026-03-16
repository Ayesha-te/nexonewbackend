from .models import BinaryNode


def serialize_node(user):
    children = {node.side: node.user for node in BinaryNode.objects.filter(parent=user)}
    return {
        "id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "position": user.placement_side or "root",
        "children": {
            "left": serialize_node(children["left"]) if "left" in children else None,
            "right": serialize_node(children["right"]) if "right" in children else None,
        },
    }


def build_tree_payload(user):
    node = BinaryNode.objects.filter(user=user).first()
    root_user = user
    while node and node.parent:
        root_user = node.parent
        node = BinaryNode.objects.filter(user=root_user).first()
    return serialize_node(root_user)


def get_children_map(user):
    return {node.side: node.user for node in BinaryNode.objects.filter(parent=user).select_related("user")}


def find_next_open_slot(root_user, preferred_side):
    current = root_user
    while True:
        children = get_children_map(current)
        if preferred_side not in children:
            return current, preferred_side
        current = children[preferred_side]
