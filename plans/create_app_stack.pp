plan bolt_appstack_cloud::create_app_stack(
  TargetSpec $targets,
  String $apps_stack_filename,
  Optional[String[1]] $generated_inventory_filename= undef,
) {
  $target1 = get_target($targets)
  out::message($target1)
  $inventory_table = run_task('bolt_appstack_cloud::create_app_stack',$targets, 'apps_stack_filename' => $apps_stack_filename,
  'generated_inventory_filename' => $generated_inventory_filename)
  $status =''
  out::message($status)
}
