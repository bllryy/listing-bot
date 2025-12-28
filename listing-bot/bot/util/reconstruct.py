def reconstruct(data: dict) -> str:
    try:
        if data['type'] != 1 or "focused" in str(data):
            return None
    except KeyError:
        raise ValueError("Invalid data (perhaps a user command).")

    command = f"/{data['name']}"
    options_stack = [data.get('options', [])]

    while options_stack:
        options = options_stack.pop()
        if not isinstance(options, list):
            options = [options]

        for option in options:
            option_type = option['type']
            option_name = option['name']
            option_value = option.get('value')

            if option_type in {1, 2}:
                command += f" {option_name}"
                nested_options = option.get('options')
                if nested_options:
                    options_stack.append(nested_options)
            elif option_type == 6:
                command += f" `{option_name}:` <@{option_value}>"
            else:
                command += f" `{option_name}: {option_value}`"

    if len(command) > 2000:
        return "Command too long to display here."

    return command