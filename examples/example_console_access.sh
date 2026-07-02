# See what console access the BMC exposes. Redfish DESCRIBES console access
# (connect types, sessions) but does not stream it — you reach the live console
# out of band using the reported connect types.
idrac_ctl console-info

# SerialConsole -> reach it over SOL (Serial Over LAN), e.g.:
#   ipmitool -I lanplus -H "$IDRAC_IP" -U "$IDRAC_USERNAME" -P "$IDRAC_PASSWORD" sol activate
#   ssh "$IDRAC_USERNAME@$IDRAC_IP"      # then start SOL from the BMC shell
# GraphicalConsole (KVMIP) -> open the BMC's HTML5/Java KVM viewer in a browser.
