const logger = {
    info(message, data = null) {
        if (data !== null) {
            console.info(`[INFO] ${message}`, data);
        } else {
            console.info(`[INFO] ${message}`);
        }
    },

    warn(message, data = null) {
        if (data !== null) {
            console.warn(`[WARN] ${message}`, data);
        } else {
            console.warn(`[WARN] ${message}`);
        }
    },

    error(message, error = null) {
        if (error !== null) {
            console.error(`[ERROR] ${message}`, error);
        } else {
            console.error(`[ERROR] ${message}`);
        }
    },

    debug(message, data = null) {
        if (data !== null) {
            console.debug(`[DEBUG] ${message}`, data);
        } else {
            console.debug(`[DEBUG] ${message}`);
        }
    }
};