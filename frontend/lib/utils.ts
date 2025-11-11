import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge and de-duplicate Tailwind/clsx class names.
 *
 * @param inputs - One or more class name values (strings, arrays, objects) accepted by clsx.
 * @returns A single space-delimited string with merged Tailwind classes.
 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}
