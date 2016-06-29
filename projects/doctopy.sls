{% from 'projects/fixtures.sls' import tmuxinator %}
{% set project = 'DoctoPy' %}
{% set prefix = salt['funwith.prefix'](project) %}
{{project}} packages:
  pkg.installed:
    - pkgs:
      - pandoc
      - graphviz
      - wget

{{prefix}}:
  virtualenv.managed:
    - python: python2
    - pip_upgrade: True
    - pip_pkgs:
      - pip
      - pandas
      - numpy
      - scipy
      - jupyter
      - matplotlib

{{project}} modulefile:
  funwith.modulefile:
    - name: {{project}}
    - prefix: {{prefix}}
    - cwd: {{prefix}}/src/{{project}}
    - virtualenv: {{project}}

UCL-RITS/doctoral-programming-intro:
  github.present:
    - target: {{prefix}}/src/{{project}}

jekyll:
  gem.installed

redcarpet:
  gem.installed

{{tmuxinator(project, root="%s/src/%s" % (prefix, project), file="crystal/__init__.py")}}
