import React from 'react';
import { NavLink, useResolvedPath } from 'react-router-dom';

/**
 * DashboardTabs — horizontal tab bar that renders NavLink pills.
 * Props:
 *   tabs: [{ label: string, to: string }]
 *   basePath: string  (the parent route path, e.g. "/dashboard/executive")
 */
export default function DashboardTabs({ tabs }) {
    return (
        <nav className="flex items-center gap-1 mb-8 p-1.5 bg-gray-100 dark:bg-white/5 rounded-2xl w-fit">
            {tabs.map((tab) => (
                <NavLink
                    key={tab.to}
                    to={tab.to}
                    end={tab.end}
                    className={({ isActive }) =>
                        `px-5 py-2 rounded-xl text-sm font-semibold transition-all ${isActive
                            ? 'bg-white dark:bg-white/10 text-gray-900 dark:text-white shadow-sm'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                        }`
                    }
                >
                    {tab.label}
                </NavLink>
            ))}
        </nav>
    );
}
