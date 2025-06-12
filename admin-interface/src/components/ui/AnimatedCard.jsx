import { motion } from 'framer-motion';
import { usePersonaAnimations } from '../../hooks/usePersonaAnimations';

export const AnimatedCard = ({ children, persona, className = "", onClick, ...props }) => {
  const animations = usePersonaAnimations(persona);
  
  return (
    <motion.div
      className={`animated-card ${persona} ${className}`}
      initial={animations.initial}
      animate={animations.animate}
      exit={animations.exit}
      whileHover={animations.hover}
      whileTap={animations.tap}
      onClick={onClick}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const AnimatedButton = ({ children, persona, className = "", onClick, disabled = false, ...props }) => {
  const animations = usePersonaAnimations(persona);
  
  return (
    <motion.button
      className={`animated-button ${persona} ${className} ${disabled ? 'disabled' : ''}`}
      initial={animations.initial}
      animate={animations.animate}
      whileHover={disabled ? {} : animations.hover}
      whileTap={disabled ? {} : animations.tap}
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </motion.button>
  );
};

export const AnimatedContainer = ({ children, persona, className = "", ...props }) => {
  const animations = usePersonaAnimations(persona);
  
  return (
    <motion.div
      className={`animated-container ${persona} ${className}`}
      initial={animations.initial}
      animate={animations.animate}
      exit={animations.exit}
      {...props}
    >
      {children}
    </motion.div>
  );
}; 