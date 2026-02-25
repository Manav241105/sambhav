import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import BayCalendar from '../../components/BayCalendar';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

export default function OpsCalendar() {
    const { bookings } = useOutletContext();

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                Bay Schedule
            </h2>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                Spatial view of the shop floor. Colour-coded blocks identify the type of service booked and the priority level.
                Use this view to ensure the correct specialist is available for upcoming slots and flag scheduling conflicts early.
            </p>
            <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl">
                <BayCalendar bookings={bookings} />
            </div>
        </motion.div>
    );
}
