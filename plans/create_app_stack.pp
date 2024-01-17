plan bolt_appstack_cloud::create_app_stack(
  TargetSpec $targets,
  String $apps_stack_filename,
  String $generated_inventory_filename,
) {
  $target1 = get_target($targets)
  out::message($target1)
  $inventory = run_task('bolt_appstack_cloud::create_app_stack',$targets, 'apps_stack_filename' => $apps_stack_filename,
  'generated_inventory_filename' => $generated_inventory_filename)
  out::message($inventory)
}
