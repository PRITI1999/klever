/*
 * Copyright (c) 2014-2016 ISPRAS (http://www.ispras.ru)
 * Institute for System Programming of the Russian Academy of Sciences
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * ee the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <linux/module.h>
#include <linux/tty.h>
#include <linux/usb.h>
#include <linux/usb/serial.h>
#include <linux/emg/test_model.h>
#include <verifier/nondet.h>

int flip_a_coin;
const struct usb_device_id *id_table;

int ldv_probe(struct usb_serial *serial, const struct usb_device_id *id)
{
	int res;

	ldv_invoke_callback();
	res = ldv_undef_int();
	if (!res)
		ldv_probe_up();
	return res;
}

void ldv_disconnect(struct usb_serial *serial)
{
	ldv_release_down();
	ldv_invoke_callback();
}

static struct usb_serial_driver ldv_driver = {
	.probe = ldv_probe,
	.disconnect = ldv_disconnect,
};

static int __init ldv_init(void)
{
	flip_a_coin = ldv_undef_int();
	if (flip_a_coin) {
		ldv_register();
		return usb_serial_register(& ldv_driver);
	}
	return 0;
}

static void __exit ldv_exit(void)
{
	if (flip_a_coin) {
		usb_serial_deregister(& ldv_driver);
		ldv_deregister();
	}
}

module_init(ldv_init);
module_exit(ldv_exit);
