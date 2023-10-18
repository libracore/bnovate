// (C) 2023, bnovate
// Simulate realtime update from the server.

frappe.provide('bnovate.realtime');

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function get_status(task_id) {
    const resp = await frappe.call({
        method: 'bnovate.bnovate.utils.realtime.get_status',
        args: {
            task_id
        }
    });
    return resp.message;
}

// Call this method first to get a task id...
bnovate.realtime.get_task_id = async function () {
    const resp = await frappe.call({
        method: 'bnovate.bnovate.utils.realtime.get_new_id',
    });
    return resp.message;
}

// ...Then register the listener using the id you received:
bnovate.realtime.on = async function (id, callback, timeout = 60 * 1000) {
    const interval = 1000;
    let running_time = 0;

    while (running_time < timeout) {
        running_time += interval;

        const status = await get_status(id);
        if (!status) {
            continue;
        }

        callback(status);

        if (status.code < 0) {
            // Sleep
            await sleep(interval);
            continue;
        } else {
            // TODO: throw error if status is > 0?
            return true;
        }
    }
    return false;
}

// Wrapper around frappe.call that can retrieve realtime updates.
// Server side method need to use set_status for messages to pass.
bnovate.realtime.call = async function ({ method, args, callback, timeout = 60 * 1000 }) {
    const task_id = await bnovate.realtime.get_task_id();
    const task = frappe.call({
        method,
        args: {
            task_id,
            ...args
        }
    });
    bnovate.realtime.on(task_id, callback, timeout);

    const resp = await task;
    return resp.message;
}