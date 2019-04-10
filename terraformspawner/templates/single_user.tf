module "{{ spawner.get_module_id() }}" {
  source = "{{ spawner.tf_module }}"
  env = {
    {%- for k,v in spawner.get_env().items() %}
    {{ k }} = "{{ v }}",
    {%- endfor %}
  }
}