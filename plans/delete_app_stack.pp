plan bolt_appstack_cloud::delete_app_stack(
  TargetSpec $targets, 
  String $generated_inventory_filename,
) {
  # parse the yaml file, get the names of the nodes
  $generated_vms = loadyaml($generated_inventory_filename)
  #out::message("Inventory: ${generated_vms}")

  $generated_vms['targets'].each |$app| {
    #out::message("Deleting ${app}")
    run_task("bolt_appstack_cloud::delete_vm", $targets, 'vm_name' => $app['name'])
  }
}
