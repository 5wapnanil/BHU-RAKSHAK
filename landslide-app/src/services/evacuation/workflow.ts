import type { EvacuationFormData, LocalEvacuationRequest } from '../../types';

export interface EvacuationValidationErrors {
  location?: string;
  numberOfPeople?: string;
  emergencyType?: string;
  contactName?: string;
  contactPhone?: string;
}

export function validateEvacuationForm(data: EvacuationFormData): EvacuationValidationErrors {
  const errors: EvacuationValidationErrors = {};

  if (!data.location.trim()) {
    errors.location = 'Please enter your current location.';
  }
  if (!data.numberOfPeople.trim()) {
    errors.numberOfPeople = 'Please enter the number of people.';
  }
  if (!data.emergencyType) {
    errors.emergencyType = 'Please select an emergency type.';
  }
  if (!data.contactName.trim()) {
    errors.contactName = 'Please enter your contact name.';
  }
  if (!data.contactPhone.trim()) {
    errors.contactPhone = 'Please enter your phone number.';
  }

  return errors;
}

export function hasEvacuationErrors(errors: EvacuationValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

/** Build the first validation error message to show in an Alert */
export function firstEvacuationError(errors: EvacuationValidationErrors): string | undefined {
  const order: (keyof EvacuationValidationErrors)[] = [
    'location',
    'numberOfPeople',
    'emergencyType',
    'contactName',
    'contactPhone',
  ];
  for (const key of order) {
    if (errors[key]) return errors[key];
  }
  return undefined;
}

export function buildEvacuationRequest(
  data: EvacuationFormData,
): Omit<LocalEvacuationRequest, 'id' | 'createdAt' | 'updatedAt' | 'syncStatus'> {
  return {
    type: 'evacuation',
    status: 'pending',
    formData: { ...data },
  };
}
