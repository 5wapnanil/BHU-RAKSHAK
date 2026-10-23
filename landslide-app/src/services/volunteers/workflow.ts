import type {
  EvacuationVolunteerFormData,
  ReliefVolunteerFormData,
  LocalEvacuationVolunteer,
  LocalReliefVolunteer,
} from '../../types';

// ── Evacuation volunteer validation ──

export interface EvacuationVolunteerValidationErrors {
  name?: string;
  phone?: string;
  currentLocation?: string;
  capabilities?: string;
}

export function validateEvacuationVolunteerForm(
  data: EvacuationVolunteerFormData,
): EvacuationVolunteerValidationErrors {
  const errors: EvacuationVolunteerValidationErrors = {};

  if (!data.name.trim()) {
    errors.name = 'Please enter your name.';
  }
  if (!data.phone.trim()) {
    errors.phone = 'Please enter your phone number.';
  }
  if (!data.currentLocation.trim()) {
    errors.currentLocation = 'Please enter your current location.';
  }
  if (data.capabilities.length === 0) {
    errors.capabilities = 'Please select at least one capability.';
  }

  return errors;
}

export function hasEvacuationVolunteerErrors(errors: EvacuationVolunteerValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function firstEvacuationVolunteerError(
  errors: EvacuationVolunteerValidationErrors,
): string | undefined {
  const order: (keyof EvacuationVolunteerValidationErrors)[] = [
    'name',
    'phone',
    'currentLocation',
    'capabilities',
  ];
  for (const key of order) {
    if (errors[key]) return errors[key];
  }
  return undefined;
}

export function buildEvacuationVolunteer(
  data: EvacuationVolunteerFormData,
): Omit<LocalEvacuationVolunteer, 'id' | 'createdAt' | 'updatedAt' | 'syncStatus'> {
  return {
    type: 'evacuation_volunteer',
    status: 'pending',
    formData: { ...data },
  };
}

// ── Relief volunteer validation ──

export interface ReliefVolunteerValidationErrors {
  name?: string;
  phone?: string;
  location?: string;
  category?: string;
}

export function validateReliefVolunteerForm(
  data: ReliefVolunteerFormData,
): ReliefVolunteerValidationErrors {
  const errors: ReliefVolunteerValidationErrors = {};

  if (!data.name.trim()) {
    errors.name = 'Please enter your name.';
  }
  if (!data.phone.trim()) {
    errors.phone = 'Please enter your phone number.';
  }
  if (!data.location.trim()) {
    errors.location = 'Please enter your location.';
  }
  if (!data.category) {
    errors.category = 'Please select a relief category.';
  }

  return errors;
}

export function hasReliefVolunteerErrors(errors: ReliefVolunteerValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function firstReliefVolunteerError(
  errors: ReliefVolunteerValidationErrors,
): string | undefined {
  const order: (keyof ReliefVolunteerValidationErrors)[] = [
    'name',
    'phone',
    'location',
    'category',
  ];
  for (const key of order) {
    if (errors[key]) return errors[key];
  }
  return undefined;
}

export function buildReliefVolunteer(
  data: ReliefVolunteerFormData,
): Omit<LocalReliefVolunteer, 'id' | 'createdAt' | 'updatedAt' | 'syncStatus'> {
  return {
    type: 'relief_volunteer',
    status: 'pending',
    formData: { ...data },
  };
}
