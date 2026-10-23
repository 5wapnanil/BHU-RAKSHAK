"use client";

import { motion, type MotionProps } from "framer-motion";
import { useReducedMotion } from "@/animations/useReducedMotion";

type Props = MotionProps & {
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
};

export function Motion({ children, style, className, ...props }: Props) {
  const reduced = useReducedMotion();

  if (reduced) {
    return (
      <div style={style} className={className}>
        {children}
      </div>
    );
  }

  return (
    <motion.div style={style} className={className} {...props}>
      {children}
    </motion.div>
  );
}
