import type { HelpFormData, LocalHelpRequest } from '../../types';

export interface HelpValidationErrors {
  category?: string;
  location?: string;
  severity?: string;
  contactName?: string;
  contactPhone?: string;
}

export function validateHelpForm(data: HelpFormData): HelpValidationErrors {
  const errors: HelpValidationErrors = {};

  if (!data.category) {
    errors.category = 'Please select a help category.';
  }
  if (!data.location.trim()) {
    errors.location = 'Please enter your location.';
  }
  if (!data.severity) {
    errors.severity = 'Please select severity level.';
  }
  if (!data.contactName.trim()) {
    errors.contactName = 'Please enter your contact name.';
  }
  if (!data.contactPhone.trim()) {
    errors.contactPhone = 'Please enter your phone number.';
  }

  return errors;
}

export function hasHelpErrors(errors: HelpValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function firstHelpError(errors: HelpValidationErrors): string | undefined {
  const order: (keyof HelpValidationErrors)[] = [
    'category',
    'location',
    'severity',
    'contactName',
    'contactPhone',
  ];
  for (const key of order) {
    if (errors[key]) return errors[key];
  }
  return undefined;
}

export function buildHelpRequest(
  data: HelpFormData,
): Omit<LocalHelpRequest, 'id' | 'createdAt' | 'updatedAt' | 'syncStatus'> {
  return {
    type: 'help',
    status: 'pending',
    formData: { ...data },
  };
}
