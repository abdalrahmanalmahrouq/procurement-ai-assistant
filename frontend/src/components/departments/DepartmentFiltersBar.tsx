import { ChevronDown, RefreshCw, Search } from 'lucide-react';
import type { DepartmentFilters } from '../../types/departments';

interface DepartmentFiltersBarProps {
  filters: DepartmentFilters;
  search: string;
  onFiltersChange: (filters: DepartmentFilters) => void;
  onSearchChange: (search: string) => void;
  onRefresh: () => void;
  onClear: () => void;
}

export function DepartmentFiltersBar({
  filters,
  search,
  onFiltersChange,
  onSearchChange,
  onRefresh,
  onClear,
}: DepartmentFiltersBarProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="w-40">
        <span className="field-label">Calendar Year</span>
        <input
          aria-label="Calendar year"
          className="form-field"
          min="1900"
          max="2100"
          placeholder="All years"
          type="number"
          value={filters.year ?? ''}
          onChange={(event) => onFiltersChange({
            ...filters,
            year: event.target.value ? Number(event.target.value) : null,
          })}
        />
      </label>

      <SelectField
        label="Quarter"
        value={filters.quarter === null ? '' : String(filters.quarter)}
        onChange={(value) => onFiltersChange({
          ...filters,
          quarter: value ? Number(value) : null,
        })}
      >
        <option value="">All quarters</option>
        {[1, 2, 3, 4].map((quarter) => <option key={quarter} value={quarter}>Q{quarter}</option>)}
      </SelectField>

      <SelectField
        label="Ranking Size"
        value={String(filters.limit)}
        onChange={(value) => onFiltersChange({ ...filters, limit: Number(value) })}
      >
        {[5, 10, 25, 50].map((limit) => <option key={limit} value={limit}>Top {limit}</option>)}
      </SelectField>

      <label className="min-w-[250px] flex-1">
        <span className="field-label">Search Loaded Departments</span>
        <span className="form-field">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            className="min-w-0 flex-1 outline-none"
            placeholder="Search by department name"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </span>
      </label>

      <button className="soft-button" onClick={onRefresh}>
        <RefreshCw className="h-4 w-4" />
        Refresh
      </button>
      <button className="h-9 text-xs font-medium text-slate-600" onClick={onClear}>Clear filters</button>
    </div>
  );
}

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}

function SelectField({ label, value, onChange, children }: SelectFieldProps) {
  return (
    <label className="w-40">
      <span className="field-label">{label}</span>
      <span className="relative block">
        <select className="form-field appearance-none pr-8" value={value} onChange={(event) => onChange(event.target.value)}>
          {children}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-3 h-3.5 w-3.5 text-slate-400" />
      </span>
    </label>
  );
}
