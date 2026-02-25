import React from 'react';
import { motion } from 'framer-motion';

const SteeringWheel3D = () => {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <motion.video
        src="/3496110955-preview.mp4"
        autoPlay
        loop
        muted
        playsInline
        className="w-full max-w-md object-contain rounded-lg"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      />
    </div>
  );
};

export default SteeringWheel3D;
