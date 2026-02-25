import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, useGLTF } from '@react-three/drei';
import { motion, AnimatePresence } from 'framer-motion';

const MODEL_PATH = '/car1.glb';

/* ── Local car GLB model ────────────────────────────── */
const Car = ({ scale = 5 }) => {
  const { scene } = useGLTF(MODEL_PATH);
  return (
    <group scale={scale} position={[0, 0, 0]}>
      <primitive object={scene} />
    </group>
  );
};

// Pre-load so the .glb starts downloading immediately
useGLTF.preload(MODEL_PATH);

/* ── Skeleton shimmer loader ──────────────────────────── */
const Loader = () => (
  <motion.div
    className="absolute inset-0 flex flex-col items-center justify-center gap-4 pointer-events-none"
    initial={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.5 }}
  >
    {/* Glowing ring shimmer */}
    <div className="relative w-32 h-32">
      <div className="absolute inset-0 rounded-full border-4 border-[#6366f1]/20 animate-pulse" />
      <div className="absolute inset-2 rounded-full border-4 border-t-[#6366f1] border-transparent animate-spin" />
      <div className="absolute inset-4 rounded-full border-2 border-t-[#6366f1]/60 border-transparent animate-spin [animation-duration:1.5s]" />
      <div className="absolute inset-0 flex items-center justify-center">
        <svg className="w-10 h-10 text-[#6366f1]/60" fill="none" viewBox="0 0 24 24">
          <path d="M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <polygon points="12 17 22 17 18 9 3 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <circle cx="7" cy="17" r="1" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="17" cy="17" r="1" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </div>
    </div>
    <div className="text-center">
      <p className="text-sm font-semibold text-[#6366f1]">Loading 3D Model</p>
      <p className="text-xs text-gray-400 mt-1">Please wait...</p>
    </div>
    {/* Progress bar */}
    <div className="w-40 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      <motion.div
        className="h-full bg-[#6366f1] rounded-full"
        animate={{ width: ['0%', '70%', '90%', '100%'] }}
        transition={{ duration: 2.5, ease: 'easeInOut', times: [0, 0.5, 0.8, 1] }}
      />
    </div>
  </motion.div>
);

/* ── Inner component that hides loader once model is ready ─ */
const SceneContent = ({ onLoaded }) => {
  return (
    <Suspense fallback={<SuspenseTrigger onLoaded={null} />}>
      <LoadedCar onLoaded={onLoaded} />
    </Suspense>
  );
};

const LoadedCar = ({ onLoaded }) => {
  React.useEffect(() => {
    // Model rendered — signal parent
    const t = setTimeout(() => onLoaded?.(), 100);
    return () => clearTimeout(t);
  }, [onLoaded]);
  return <Car />;
};

const SuspenseTrigger = () => null;

/* ── Main exported component ────────────────────────── */
const CarModel = () => {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className="relative w-full h-full">
      {/* Loader overlay */}
      <AnimatePresence>
        {!loaded && <Loader key="loader" />}
      </AnimatePresence>

      <Canvas
        style={{ background: 'transparent', opacity: loaded ? 1 : 0, transition: 'opacity 0.6s ease' }}
        gl={{ alpha: true, antialias: true }}
        camera={{ position: [4, 2.5, 4], fov: 50 }}
      >
        <Suspense fallback={null}>
          <Stage
            preset="rembrandt"
            intensity={0.6}
            environment="city"
            adjustCamera={1}
          >
            <LoadedCar onLoaded={() => setLoaded(true)} />
          </Stage>
        </Suspense>

        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={0.8}
          minPolarAngle={Math.PI / 3}
          maxPolarAngle={Math.PI / 2.2}
        />
      </Canvas>
    </div>
  );
};

export default CarModel;
