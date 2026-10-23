import type { ReliefFormData, LocalReliefRequest } from '../../types';

export interface ReliefValidationErrors {
  location?: string;
  reliefCategory?: string;
  requiredItems?: string;
  peopleAffected?: string;
  severity?: string;
  contactName?: string;
  contactPhone?: string;
}

export function validateReliefForm(data: ReliefFormData): ReliefValidationErrors {
  const errors: ReliefValidationErrors = {};

  if (!data.location.trim()) {
    errors.location = 'Please enter your location.';
  }
  if (!data.reliefCategory) {
    errors.reliefCategory = 'Please select a relief category.';
  }
  if (!data.requiredItems.trim()) {
    errors.requiredItems = 'Please specify what relief items are needed.';
  }
  if (data.peopleAffected && isNaN(parseInt(data.peopleAffected))) {
    errors.peopleAffected = 'Please enter a valid number.';
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

export function hasReliefErrors(errors: ReliefValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function firstReliefError(errors: ReliefValidationErrors): string | undefined {
  const order: (keyof ReliefValidationErrors)[] = [
    'location',
    'reliefCategory',
    'requiredItems',
    'peopleAffected',
    'severity',
    'contactName',
    'contactPhone',
  ];
  for (const key of order) {
    if (errors[key]) return errors[key];
  }
  return undefined;
}

export function buildReliefRequest(
  data: ReliefFormData,
): Omit<LocalReliefRequest, 'id' | 'createdAt' | 'updatedAt' | 'syncStatus'> {
  return {
    type: 'relief',
    status: 'pending',
    formData: { ...data },
  };
}