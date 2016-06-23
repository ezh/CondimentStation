{% macro tmuxinator(project, root="", file="", layout="main-horizontal") -%}
{{grains['userhome']}}/.tmuxinator/{{project}}.yml:
  file.managed:
    - contents: |
        name: {{project}}
        root: {{"%s/src/%s" % (salt['funwith.prefix'](project), project) if root == "" else root}}
        pre_window: module load {{project}} && fc -R
        windows:
          - {{project}}:
              layout: {{layout}}
              panes:
                - vim:
                  - vim {{file}}
                - build:
                  -
{%- endmacro %}
