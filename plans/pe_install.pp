plan bolt_appstack_cloud::pe_install(
  TargetSpec $target,
  String $plan_params_filename,
  Optional[Hash] $args = undef,
)
{
  out::message("PE_Install: ")
  
  $peadm_install_plan="peadm::install"
  
  #out::message($target.config)

  $peadm_args_hash = loadjson($plan_params_filename)
  $target_hash = {'primary_host' => $target}
  $args_hash = $peadm_args_hash + $target_hash
  run_plan($peadm_install_plan,$args_hash )
}
