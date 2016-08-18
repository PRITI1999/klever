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
#include <linux/device.h>
#include <linux/rtc.h>
#include <linux/emg/test_model.h>
#include <verifier/nondet.h>

struct device *dev;
struct rtc_device *rtc;

static int ldv_read_time(struct device *dev, struct rtc_time *tm)
{
	ldv_invoke_reached();
    return 0;
}

static const struct rtc_class_ops ldv_ops = {
	.read_time = ldv_read_time,
};

static int __init ldv_init(void)
{
	rtc = rtc_device_register("rtc-ldv", &dev, &ldv_ops, THIS_MODULE);
    if (IS_ERR(rtc))
        return PTR_ERR(rtc);
}

static void __exit ldv_exit(void)
{
	rtc_device_unregister(rtc);
}

module_init(ldv_init);
module_exit(ldv_exit);
