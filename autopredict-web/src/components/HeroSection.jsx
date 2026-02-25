import React from 'react';
import { ChevronsRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import CarModel from './CarModel';
import ThemeToggle from './ThemeToggle';
import SteeringWheel3D from './SteeringWheel3D';
import Engine3D from './Engine3D';

/* ── Spring config shared by headline elements ──────── */
const heroSpring = {
  type: 'spring',
  stiffness: 100,
  damping: 10,
  bounce: 0.4,
};

/* ── Headline: dramatic slide-up with spring physics ── */
const headlineContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.05,
    },
  },
};

const headlineWord = {
  hidden: { opacity: 0, y: 100 },
  visible: {
    opacity: 1,
    y: 0,
    transition: heroSpring,
  },
};

/* ── Subheadline: fade-up after headline finishes ───── */
const subheadlineVariants = {
  hidden: { opacity: 0, y: 60 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      delay: 0.4,
      duration: 0.7,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  },
};

/* ── CTA: spring entrance + infinite float ──────────── */
const ctaEntrance = {
  hidden: { opacity: 0, y: 80 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { ...heroSpring, delay: 0.55 },
  },
};

const ctaFloat = {
  y: [0, -8, 0],
  transition: {
    duration: 2.5,
    repeat: Infinity,
    repeatType: 'loop',
    ease: 'easeInOut',
  },
};

/* ── Stats: slide in from the left at the end ───────── */
const statsVariants = {
  hidden: { opacity: 0, x: -50 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      delay: 0.8,
      type: 'spring',
      stiffness: 80,
      damping: 14,
    },
  },
};

/* ── Nav: gentle drop-in ────────────────────────────── */
const navVariants = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: 'easeOut' },
  },
};

const HeroSection = () => {
  return (
    <div className="min-h-screen bg-[#f4f5f0] dark:bg-[#0b0f19] text-gray-900 dark:text-white font-sans overflow-hidden transition-colors duration-300">
      {/* Navigation */}
      <motion.nav
        variants={navVariants}
        initial="hidden"
        animate="visible"
        className="flex items-center justify-between px-6 py-8 mx-auto max-w-7xl lg:px-12"
      >
        <div className="flex items-center text-2xl tracking-tight">
          <span className="font-extrabold text-gray-900 dark:text-white">Auto</span>
          <span className="font-medium text-gray-500 dark:text-gray-400">Predict</span>
        </div>

        <div className="hidden space-x-8 text-sm font-medium text-gray-500 dark:text-gray-400 md:flex">
          <a href="#features" className="hover:text-gray-900 dark:hover:text-white transition-colors">AI Diagnostics</a>
          <a href="#scheduling" className="hover:text-gray-900 dark:hover:text-white transition-colors">Agent Scheduling</a>
          <a href="#dashboards" className="hover:text-gray-900 dark:hover:text-white transition-colors">Dashboards</a>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link
            to="/login"
            className="hidden px-5 py-2 text-sm font-semibold transition-colors border border-gray-300 dark:border-gray-600 rounded-full md:block hover:border-gray-900 dark:hover:border-gray-300 dark:text-white"
          >
            Login
          </Link>
        </div>
      </motion.nav>

      {/* Main Hero Content */}
      <main className="flex flex-col-reverse items-center px-6 py-12 mx-auto max-w-7xl lg:px-12 lg:flex-row lg:py-24 gap-14">

        {/* Left Column: Text & CTA — rich spring animations */}
        <div className="flex flex-col items-start w-full lg:w-1/2">

          {/* ── Headline ── */}
          <motion.h1
            className="text-4xl font-extrabold leading-tight tracking-tighter md:text-6xl lg:text-7xl"
            variants={headlineContainer}
            initial="hidden"
            animate="visible"
          >
            <motion.span
              className="inline-block cursor-pointer"
              variants={headlineWord}
              whileHover={{ y: -5, color: '#6366f1', transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              AutoPredict
            </motion.span>
            <br />
            <motion.span
              className="inline-block font-medium text-gray-400 dark:text-gray-500 cursor-pointer"
              variants={headlineWord}
              whileHover={{ y: -5, color: '#6366f1', transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              Smart Vehicle
            </motion.span>
            <br />
            <motion.span
              className="inline-block font-medium text-gray-400 dark:text-gray-500 cursor-pointer"
              variants={headlineWord}
              whileHover={{ y: -5, color: '#6366f1', transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              Diagnostics
            </motion.span>
          </motion.h1>

          {/* ── Subheadline ── */}
          <motion.p
            variants={subheadlineVariants}
            initial="hidden"
            animate="visible"
            whileHover={{ x: 5, color: '#111827', transition: { duration: 0.2, ease: 'easeOut' } }}
            className="max-w-lg mt-6 text-lg leading-relaxed text-gray-500 dark:text-gray-400 md:text-xl cursor-pointer"
          >
            AutoPredict is a modern AI-driven platform that gives you quick, real-time insights into your vehicle's health, automated scheduling, and predictive maintenance alerts.
          </motion.p>

          {/* ── CTA Button ── */}
          <motion.div
            variants={ctaEntrance}
            initial="hidden"
            animate="visible"
            className="mt-10 flex items-center"
          >
            <motion.button
              animate={ctaFloat}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center justify-center gap-3 px-8 py-4 text-lg font-bold text-white bg-[#6366f1] rounded-tl-full rounded-bl-full rounded-tr-xl rounded-br-[3rem] shadow-sm hover:bg-[#4f46e5] transition-colors"
            >
              Start Diagnostics
              <ChevronsRight className="w-6 h-6" />
            </motion.button>
          </motion.div>

          {/* ── Stats ── */}
          <motion.div
            variants={statsVariants}
            initial="hidden"
            animate="visible"
            className="flex items-center gap-8 mt-16 text-sm font-medium text-gray-400 dark:text-gray-500"
          >
            <motion.div
              className="flex flex-col cursor-pointer"
              whileHover={{ scale: 1.05, transition: { type: 'spring', stiffness: 300, damping: 12 } }}
            >
              <span className="text-2xl font-bold text-gray-900 dark:text-white">99%</span>
              <span>Prediction Accuracy</span>
            </motion.div>
            <div className="w-px h-10 bg-gray-300 dark:bg-gray-700"></div>
            <motion.div
              className="flex flex-col cursor-pointer"
              whileHover={{ scale: 1.05, transition: { type: 'spring', stiffness: 300, damping: 12 } }}
            >
              <span className="text-2xl font-bold text-gray-900 dark:text-white">24/7</span>
              <span>AI Agent Support</span>
            </motion.div>
          </motion.div>
        </div>

        {/* Right Column: Interactive 3D Car (no zoom) */}
        <motion.div
          className="relative flex items-center justify-center w-full lg:w-1/2 h-[500px] lg:h-[700px] overflow-visible"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
        >
          <div className="absolute top-0 right-0 w-3/4 bg-white dark:bg-gray-800 rounded-full h-3/4 blur-3xl opacity-60 -z-10"></div>
          <CarModel />
        </motion.div>
      </main>

      {/* Vision Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6 lg:px-12 grid md:grid-cols-2 gap-16 items-center">

          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="relative p-8 bg-white dark:bg-gray-800 rounded-3xl shadow-lg border border-gray-200 dark:border-gray-700"
          >
            <div className="absolute -inset-1 bg-gradient-to-r from-[#6366f1] to-transparent opacity-20 blur-xl rounded-3xl -z-10"></div>
            <motion.h2
              className="text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white mb-6 cursor-pointer"
              whileHover={{ y: -5, color: '#6366f1', transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              Our Vision
            </motion.h2>
            <motion.p
              className="text-lg leading-relaxed text-gray-500 dark:text-gray-400 cursor-pointer"
              whileHover={{ x: 5, transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              To revolutionize vehicle maintenance through AI-powered predictive diagnostics, making car care effortless, transparent, and accessible for everyone. We envision a future where vehicle breakdowns are prevented before they happen.
            </motion.p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="flex justify-center"
          >
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              whileHover={{ scale: 1.05 }}
              className="w-full max-w-md h-80 transition-transform duration-500"
            >
              <SteeringWheel3D />
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6 lg:px-12 grid md:grid-cols-2 gap-16 items-center">

          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="flex justify-center order-2 md:order-1"
          >
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
              whileHover={{ scale: 1.05 }}
              className="w-full max-w-md h-80 transition-transform duration-500"
            >
              <Engine3D />
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="order-1 md:order-2 relative p-8 bg-white dark:bg-gray-800 rounded-3xl shadow-lg border border-gray-200 dark:border-gray-700"
          >
            <div className="absolute -inset-1 bg-gradient-to-r from-[#6366f1] to-transparent opacity-20 blur-xl rounded-3xl -z-10"></div>
            <motion.h2
              className="text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white mb-6 cursor-pointer"
              whileHover={{ y: -5, color: '#6366f1', transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              Our Mission
            </motion.h2>
            <motion.p
              className="text-lg leading-relaxed text-gray-500 dark:text-gray-400 cursor-pointer"
              whileHover={{ x: 5, transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              To empower vehicle owners with intelligent, real-time insights into their vehicle's health. Through cutting-edge AI technology and automated scheduling, we deliver predictive maintenance alerts that save time, money, and ensure safety on the road.
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* Reviews Section */}
      <section className="py-24 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="text-center mb-16"
          >
            <motion.h2
              className="text-5xl font-extrabold tracking-tight text-gray-900 dark:text-white mb-4 cursor-pointer inline-block"
              whileHover={{ y: -5, color: '#6366f1', transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              What Our Users Say
            </motion.h2>
            <motion.p
              className="text-lg text-gray-500 dark:text-gray-400 cursor-pointer"
              whileHover={{ x: 5, transition: { duration: 0.2, ease: 'easeOut' } }}
            >
              Trusted by thousands of vehicle owners worldwide
            </motion.p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                initials: 'JD', name: 'John Doe', role: 'Tesla Model 3 Owner',
                text: '"AutoPredict saved me from a major breakdown! The AI predicted my brake issue before it became dangerous. Absolutely incredible technology."',
              },
              {
                initials: 'SM', name: 'Sarah Miller', role: 'BMW X5 Owner',
                text: '"The automated scheduling feature is a game-changer. No more forgetting oil changes or maintenance appointments. My car has never run better!"',
              },
              {
                initials: 'MJ', name: 'Michael Johnson', role: 'Audi A4 Owner',
                text: '"Real-time diagnostics at my fingertips! I love how the AI agent explains everything in simple terms. It\'s like having a mechanic in my pocket."',
              },
            ].map((r, i) => (
              <motion.div
                key={r.name}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: i * 0.1 }}
                whileHover={{ y: -10, transition: { duration: 0.3 } }}
                className="relative p-8 bg-[#f4f5f0] dark:bg-gray-800 rounded-3xl shadow-lg border border-gray-200 dark:border-gray-700 cursor-pointer"
              >
                <div className="absolute -inset-1 bg-gradient-to-r from-[#6366f1] to-transparent opacity-10 blur-xl rounded-3xl -z-10"></div>
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, j) => (
                    <svg key={j} className="w-5 h-5 text-[#6366f1]" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">{r.text}</p>
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-[#6366f1] rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {r.initials}
                  </div>
                  <div className="ml-4">
                    <p className="font-bold text-gray-900 dark:text-white">{r.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{r.role}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0b0f19] text-white py-16">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="grid md:grid-cols-4 gap-12 mb-12">

            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6, ease: 'easeOut' }}>
              <div className="flex items-center text-2xl tracking-tight mb-4">
                <span className="font-extrabold text-white">Auto</span>
                <span className="font-medium text-gray-400">Predict</span>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed">AI-powered vehicle diagnostics and predictive maintenance for the modern driver.</p>
            </motion.div>

            {[
              { title: 'Product', links: [['AI Diagnostics', '#features'], ['Agent Scheduling', '#scheduling'], ['Dashboards', '#dashboards'], ['Pricing', '#pricing']] },
              { title: 'Company', links: [['About Us', '#about'], ['Careers', '#careers'], ['Blog', '#blog'], ['Contact', '#contact']] },
              { title: 'Legal', links: [['Privacy Policy', '#privacy'], ['Terms of Service', '#terms'], ['Cookie Policy', '#cookies']] },
            ].map((col, i) => (
              <motion.div key={col.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6, ease: 'easeOut', delay: (i + 1) * 0.1 }}>
                <h3 className="font-bold text-lg mb-4">{col.title}</h3>
                <ul className="space-y-2 text-gray-400 text-sm">
                  {col.links.map(([label, href]) => (
                    <motion.li key={label} whileHover={{ x: 5, color: '#6366f1', transition: { duration: 0.2 } }} className="cursor-pointer">
                      <a href={href}>{label}</a>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ duration: 0.6, ease: 'easeOut', delay: 0.4 }}
            className="pt-8 border-t border-gray-800 flex flex-col md:flex-row justify-between items-center gap-4"
          >
            <p className="text-gray-400 text-sm">© 2024 AutoPredict. All rights reserved.</p>
            <div className="flex gap-6">
              {/* Twitter */}
              <motion.a href="#twitter" whileHover={{ y: -3, color: '#6366f1', transition: { duration: 0.2 } }} className="text-gray-400 transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg>
              </motion.a>
              {/* LinkedIn */}
              <motion.a href="#linkedin" whileHover={{ y: -3, color: '#6366f1', transition: { duration: 0.2 } }} className="text-gray-400 transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" /></svg>
              </motion.a>
              {/* GitHub */}
              <motion.a href="#github" whileHover={{ y: -3, color: '#6366f1', transition: { duration: 0.2 } }} className="text-gray-400 transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
              </motion.a>
            </div>
          </motion.div>
        </div>
      </footer>
    </div>
  );
};

export default HeroSection;
