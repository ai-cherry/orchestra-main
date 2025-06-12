import { useAnimation } from 'framer-motion';

export const usePersonaAnimations = (persona) => {
  const controls = useAnimation();
  
  const animations = {
    cherry: {
      initial: { opacity: 0, y: 20, scale: 0.9 },
      animate: { 
        opacity: 1, 
        y: 0, 
        scale: 1,
        transition: { 
          type: "spring", 
          stiffness: 300, 
          damping: 20,
          duration: 0.6
        }
      },
      exit: { opacity: 0, y: -20, transition: { duration: 0.3 } },
      hover: { scale: 1.02, transition: { duration: 0.2 } },
      tap: { scale: 0.98 }
    },
    sophia: {
      initial: { opacity: 0, x: -20 },
      animate: { 
        opacity: 1, 
        x: 0,
        transition: { 
          type: "tween", 
          ease: "easeOut", 
          duration: 0.4 
        }
      },
      exit: { opacity: 0, x: 20, transition: { duration: 0.3 } },
      hover: { x: 2, transition: { duration: 0.2 } },
      tap: { x: -2 }
    },
    karen: {
      initial: { opacity: 0, scale: 0.95 },
      animate: { 
        opacity: 1, 
        scale: 1,
        transition: { 
          type: "spring", 
          stiffness: 400, 
          damping: 25,
          duration: 0.5
        }
      },
      exit: { opacity: 0, scale: 0.9, transition: { duration: 0.2 } },
      hover: { scale: 1.01, transition: { duration: 0.15 } },
      tap: { scale: 0.99 }
    }
  };
  
  return animations[persona] || animations.cherry;
};

export const usePageTransition = () => {
  return {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: { duration: 0.3 }
  };
};

export const useStaggeredAnimation = (delay = 0.1) => {
  return {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.3, delay }
  };
}; 