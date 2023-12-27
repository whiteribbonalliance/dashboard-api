import os

import yaml


# Note: Edited to allow support for build_env_variables
def replace_env_variables_in_app_yaml_file():
    github_workspace = os.environ.get("GITHUB_WORKSPACE")
    app_yaml_path = os.environ.get("INPUT_APP_YAML_PATH")

    # Open file
    yaml_file = os.path.join(github_workspace, app_yaml_path)
    with open(yaml_file, "r") as file:
        yaml_data = yaml.safe_load(file)

    # Check if section exists
    has_env_variables = False
    if "env_variables" in yaml_data:
        has_env_variables = True
    has_build_env_variables = False
    if "build_env_variables" in yaml_data:
        has_build_env_variables = True

    if not has_env_variables and not has_build_env_variables:
        raise Exception(
            "Cannot find the env_variables section and the build_env_variables section in yaml file."
        )

    def replace(section: str):
        for key in yaml_data[section]:
            env_var = yaml_data[section][key]
            if type(env_var) is str and env_var.startswith("$"):
                repl_env_var = os.environ.get(env_var[1:])
                if repl_env_var is not None:
                    yaml_data[section][key] = repl_env_var
                else:
                    raise Exception(
                        f"Cannot find the env variable {env_var[1:]} in the section in github workflow."
                    )

    # Replace env variables
    if has_env_variables:
        replace(section="env_variables")
    if has_build_env_variables:
        replace(section="build_env_variables")

    # Save file
    with open(yaml_file, "w") as file:
        yaml.dump(yaml_data, file)


if __name__ == "__main__":
    replace_env_variables_in_app_yaml_file()
