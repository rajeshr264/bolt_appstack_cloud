plan bolt_appstack_cloud::create_app_stack(
  TargetSpec $targets,
  String $apps_stack_filename,
  String $generated_inventory_filename
) {
    
  $inventory_json = run_task('bolt_appstack_cloud::create_app_stack', $targets, 'apps_stack_filename' => $apps_stack_filename,
  'generated_inventory_filename' => $generated_inventory_filename)

  # for debug
  #$inventory_json = run_task('bolt_appstack_cloud::test_create_app_stack',$targets)
  #out::message("Returned Inventory: ")
  #out::message($inventory_json)

  # Bolt returns ResultSet data structure. 
  # Use the ResultSet APIs to parse the generated inventory file and create a new TargetSpec to pass to the run_plan command

  $apps = $inventory_json.first().to_data()['value']['vms']
  #out::message("Apps: ")
  #out::message($apps)
  #out::message(stdlib::type_of($apps))

  # the last item in app list is the 'config' section
  $config_section = $apps[-1]
  #out::message($config_section)

  $apps.each |$app| {
    if $app["name"] { # 'config' section has no 'name' key
      # create the Target
      $target = get_target($app["name"])
      set_config($target, 'transport', 'ssh') # hardcoded for now
      set_config($target, 'ssh', { user => $config_section['config']['ssh']['user'], private-key => $config_section['config']['ssh']['private-key'],
      native-ssh => true, run-as => 'root'})

      # out::message("Target: ")
      out::message($target)
      $plan_name = String.new($app['plan'])
      # out::message("Plan params: ")
      # out::message($app['plan_params'])

      run_plan($plan_name, 'target' => $target, 'plan_params_filename' => $app['plan_params'])
    }
  }
}
