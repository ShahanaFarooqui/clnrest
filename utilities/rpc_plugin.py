import os
from multiprocessing import Manager
from pyln.client import Plugin

plugin = Plugin()
manager = Manager()
queue = manager.Queue()

plugin.add_option(name="rest_certs_path", default=os.getcwd(), description="Path for certificates (for https)", opt_type="string", deprecated=False)
plugin.add_option(name="rest_protocol", default="https", description="REST server protocol", opt_type="string", deprecated=False)
plugin.add_option(name="rest_host", default="127.0.0.1", description="REST server host", opt_type="string", deprecated=False)
plugin.add_option(name="rest_port", default=3010, description="REST server port to listen", opt_type="int", deprecated=False)

def add_notifications(event, message):
    queue.put(str({"event": event, "notification": str(message)}) + "\n")

@plugin.subscribe("channel_opened")
def subscription_handler(plugin, channel_opened, **kwargs):
    plugin.log("Notification for channel open: {}".format(channel_opened), "info")
    add_notifications("channel_opened", channel_opened)

@plugin.subscribe("channel_open_failed")
def subscription_handler(plugin, channel_open_failed, **kwargs):
    plugin.log("Notification for channel open failed: {}".format(channel_open_failed), "info")
    add_notifications("channel_open_failed", channel_open_failed)

@plugin.subscribe("channel_state_changed")
def subscription_handler(plugin, channel_state_changed, **kwargs):
    plugin.log("Notification for channel state changed: {}".format(channel_state_changed), "info")
    add_notifications("channel_state_changed", channel_state_changed)

@plugin.subscribe("connect")
def subscription_handler(plugin, connect, **kwargs):
    plugin.log("Notification for connect: {}".format(connect), "info")
    add_notifications("connect", connect)

@plugin.subscribe("disconnect")
def subscription_handler(plugin, disconnect, **kwargs):
    plugin.log("Notification for disconnect: {}".format(disconnect), "info")
    add_notifications("disconnect", disconnect)

@plugin.subscribe("invoice_payment")
def subscription_handler(plugin, invoice_payment, **kwargs):
    plugin.log("Notification for invoice payment: {}".format(invoice_payment), "info")
    add_notifications("invoice_payment", invoice_payment)

@plugin.subscribe("invoice_creation")
def subscription_handler(plugin, invoice_creation, **kwargs):
    plugin.log("Notification for invoice creation: {}".format(invoice_creation), "info")
    add_notifications("invoice_creation", invoice_creation)

@plugin.subscribe("warning")
def subscription_handler(plugin, warning, **kwargs):
    plugin.log("Notification for warning: {}".format(warning), "info")
    add_notifications("warning", warning)

@plugin.subscribe("forward_event")
def subscription_handler(plugin, forward_event, **kwargs):
    plugin.log("Notification for forward event: {}".format(forward_event), "info")
    add_notifications("forward_event", forward_event)

@plugin.subscribe("sendpay_success")
def subscription_handler(plugin, sendpay_success, **kwargs):
    plugin.log("Notification for send pay success: {}".format(sendpay_success), "info")
    add_notifications("sendpay_success", sendpay_success)

@plugin.subscribe("sendpay_failure")
def subscription_handler(plugin, sendpay_failure, **kwargs):
    plugin.log("Notification for send pay failure: {}".format(sendpay_failure), "info")
    add_notifications("sendpay_failure", sendpay_failure)

@plugin.subscribe("coin_movement")
def subscription_handler(plugin, coin_movement, **kwargs):
    plugin.log("Notification for coin movement: {}".format(coin_movement), "info")
    add_notifications("coin_movement", coin_movement)

@plugin.subscribe("balance_snapshot")
def subscription_handler(plugin, balance_snapshot, **kwargs):
    plugin.log("Notification for balance snapshot: {}".format(balance_snapshot), "info")
    add_notifications("balance_snapshot", balance_snapshot)

@plugin.subscribe("block_added")
def subscription_handler(plugin, block_added, **kwargs):
    plugin.log("Notification for block added: {}".format(block_added), "info")
    add_notifications("block_added", block_added)

@plugin.subscribe("openchannel_peer_sigs")
def subscription_handler(plugin, openchannel_peer_sigs, **kwargs):
    plugin.log("Notification for open channel peer sigs: {}".format(openchannel_peer_sigs), "info")
    add_notifications("openchannel_peer_sigs", openchannel_peer_sigs)

@plugin.subscribe("shutdown")
def subscription_handler(plugin, **kwargs):
    plugin.log("Notification for shutdown", "info")
    add_notifications("shutdown", "Shutdown")
