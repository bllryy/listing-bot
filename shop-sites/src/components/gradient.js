import React from 'react';

/**
 * GradientText component that renders text with a gradient effect
 * @param {string} text - The text to display
 * @param {string} startColor - The starting color of the gradient (hex, rgb, etc.)
 * @param {string} endColor - The ending color of the gradient (hex, rgb, etc.)
 * @param {string} className - Additional CSS classes
 * @param {object} props - Additional props to pass to the component
 */
const GradientText = ({ 
  text, 
  startColor = "#ff4d4d", 
  endColor = "#4d79ff",
  className = "",
  ...props 
}) => {
  const gradientStyle = {
    background: `linear-gradient(to right, ${startColor}, ${endColor})`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    color: 'transparent', // Fallback
    display: 'inline-block'
  };

  return (
    <span 
      style={gradientStyle} 
      className={className}
      {...props}
    >
      {text}
    </span>
  );
};

export default GradientText;