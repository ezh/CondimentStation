{% from 'projects/fixtures.sls' import tmuxinator %}
{% set project = "blackgarlic" %}
{% set prefix = salt['funwith.prefix'](project) %}

{{prefix}}:
  file.directory:
    - makedirs: True

{{project}} modulefile:
  funwith.modulefile:
    - name: {{project}}
    - prefix: {{prefix}}
    - cwd: {{prefix}}
    - virtualenv: {{project}}/build/salt-env

mdavezac/CondimentStation:
  github.present:
    - target: {{prefix}}

{{tmuxinator(project, root=prefix)}}
