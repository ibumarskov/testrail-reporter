import re


def perform_actions(string, actions):
    out = ''
    for action in actions:
        if 'custom_map' in action:
            for key, pattern in action['custom_map'].items():
                if re.match(pattern, string):
                    out += key
        if 'find' in action:
            f = re.findall(action['find'], string)
            if not f:
                return None
            elif len(f) > 1:
                Exception("Was found more than one match: {}".format(f))
            else:
                out += f[0]
        if 'replace' in action:
            out = out.replace(action['replace']['old'],
                              action['replace']['new'])
    return out
