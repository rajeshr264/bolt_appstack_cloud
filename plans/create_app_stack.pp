plan bolt_appstack_cloud::create_app_stack(
  TargetSpec $targets,
  String $apps_stack_filename,
  String $generated_inventory_filename
) {
  # $inventory_json = run_task('bolt_appstack_cloud::create_app_stack', $targets, 'apps_stack_filename' => $apps_stack_filename,
  # 'generated_inventory_filename' => $generated_inventory_filename)

  # for debug
  $inventory_json = run_task('bolt_appstack_cloud::test_create_app_stack',$targets)
  #out::message($inventory_json)

  $inventory_json.each |$result| {
    $node_list = $result.value['values']
    #out::message("nodelist: ${node_list}")
    $node_list.each |$node| {
      $plan_params = loadjson($node['plan_params'])

      #out::message($hash)
      #out::message("  ")
      #out::message($node)
      $target = TargetSpec.new($node["name"])
      $plan_name = String.new($node['plan'])

      #out::message("Plan : ${plan_name} Target: ${target} Params: ${plan_params}")

      run_plan($plan_name, $target, $plan_params)
    }
  }
}
