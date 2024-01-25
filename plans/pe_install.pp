plan bolt_appstack_cloud::pe_install(
  TargetSpec $target,
  String $plan_params_filename,
  Optional[Hash] $args = undef,
)
{
  #out::message("PE_Install: ")
  
  $peadm_install_plan="peadm::install"
  
  #out::message($target.config)

  $peadm_args_hash = loadjson($plan_params_filename)
  $target_hash = {'primary_host' => $target}
  $args_hash = $peadm_args_hash + $target_hash

  # Wierd Situation: for freshly created VMs, bolt/ssh is not able to connect to the VM. Hence have to run it twice.
  $result_or_error = catch_errors(['bolt/run-failure']) || {
    run_plan($peadm_install_plan,$args_hash)
  }
  if $result_or_error =~ Error {
    $msg = $result_or_error.details['result_set'][0].error().message()
    if $msg =~ 'No route to host' { # this is the SSH error message when connecting first time.
      run_plan($peadm_install_plan,$args_hash) # run peadm::install again
    } else {
      fail_plan($result_or_error)
    }
  }
}
