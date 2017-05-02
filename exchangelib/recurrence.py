import logging

from six import string_types

from .fields import IntegerField, EnumField, EnumListField, DateField, DateTimeField, EWSElementField
from .folders import EWSElement
from .properties import ItemId

log = logging.getLogger(__name__)


# DayOfWeekIndex enum. See https://msdn.microsoft.com/en-us/library/office/aa581350(v=exchg.150).aspx
FIRST = 'First'
SECOND = 'Second'
THIRD = 'Third'
FOURTH = 'Fourth'
LAST = 'Last'
WEEK_NUMBERS = (FIRST, SECOND, THIRD, FOURTH, LAST)

# Month enum
JANUARY = 'January'
FEBRUARY = 'February'
MARCH = 'March'
APRIL = 'April'
MAY = 'May'
JUNE = 'June'
JULY = 'July'
AUGUST = 'August'
SEPTEMBER = 'September'
OCTOBER = 'October'
NOVEMBER = 'November'
DECEMBER = 'December'
MONTHS = (JANUARY, FEBRUARY, MARCH, APRIL, MAY, JUNE, JULY, AUGUST, SEPTEMBER, OCTOBER, NOVEMBER, DECEMBER)

# Weekday enum
MONDAY = 'Monday'
TUESDAY = 'Tuesday'
WEDNESDAY = 'Wednesday'
THURSDAY = 'Thursday'
FRIDAY = 'Friday'
SATURDAY = 'Saturday'
SUNDAY = 'Sunday'
WEEKDAY_NAMES = (MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY)

# Used for weekday recurrences except weekly recurrences. E.g. for "First WeekendDay in March"
DAY = 'Day'
WEEK_DAY = 'Weekday'  # Non-weekend day
WEEKEND_DAY = 'WeekendDay'
EXTRA_WEEKDAY_OPTIONS = (DAY, WEEK_DAY, WEEKEND_DAY)

# DaysOfWeek enum: See https://msdn.microsoft.com/en-us/library/office/ee332417(v=exchg.150).aspx
WEEKDAYS = WEEKDAY_NAMES + EXTRA_WEEKDAY_OPTIONS


class ExtraWeekdaysField(EnumListField):
    def __init__(self, *args, **kwargs):
        kwargs['enum'] = WEEKDAYS
        super(ExtraWeekdaysField, self).__init__(*args, **kwargs)

    def clean(self, value, version=None):
        # Pass EXTRA_WEEKDAY_OPTIONS as single string or integer value
        if isinstance(value, string_types):
            if value not in EXTRA_WEEKDAY_OPTIONS:
                raise ValueError(
                    "Single value '%s' on field '%s' must be one of %s" % (value, self.name, EXTRA_WEEKDAY_OPTIONS))
            value = [self.enum.index(value) + 1]
        elif isinstance(value, self.value_cls):
            value = [value]
        else:
            value = list(value)  # Convert to something we can index
            for i, v in enumerate(value):
                if isinstance(value, string_types):
                    if v not in WEEKDAY_NAMES:
                        raise ValueError(
                            "List value '%s' on field '%s' must be one of %s" % (v, self.name, WEEKDAY_NAMES))
                    value[i] = self.enum.index(v) + 1
                elif isinstance(v, self.value_cls) and not 1 <= v <= 7:
                    raise ValueError("List value '%s' on field '%s' must be in range 1 -> 7" % (v, self.name))
        return super(ExtraWeekdaysField, self).clean(value, version=version)


class Pattern(EWSElement):
    pass


class AbsoluteYearlyPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa564242(v=exchg.150).aspx
    ELEMENT_NAME = 'AbsoluteYearlyRecurrence'

    FIELDS = [
        # The month of the year, from 1 - 12
        EnumField('month', field_uri='t:Month', enum=MONTHS),
        # The day of month of an occurrence, in range 1 -> 31. If a particular month has less days than the day_of_month
        # value, the last day in the month is assumed
        IntegerField('day_of_month', field_uri='t:DayOfMonth', min=1, max=31),
    ]

    def __str__(self):
        return 'Occurs on the %s. day of %s' % (self.day_of_month, MONTHS[self.month-1])


class RelativeYearlyPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/bb204113(v=exchg.150).aspx
    ELEMENT_NAME = 'RelativeYearlyRecurrence'

    FIELDS = [
        # The month of the year, from 1 - 12
        EnumField('month', field_uri='t:Month', enum=MONTHS),
        # Week number of the month, in range 1 -> 5. If 5 is specified, this assumes the last week of the month for
        # months that have only 4 weeks
        EnumField('week_number', field_uri='t:DayOfWeekIndex', enum=WEEK_NUMBERS),
        # List of valid ISO 8601 weekdays, as list of numbers in range 1 -> 7 (1 being Monday). Alternatively, weekdays
        # can be one of the DAY (or 8), WEEK_DAY (or 9) or WEEKEND_DAY (or 10) consts which is interpreted as the first
        # day, weekday, or weekend day in the month, respectively.
        ExtraWeekdaysField('weekdays', field_uri='t:DaysOfWeek'),
    ]

    def __str__(self):
        return 'Occurs on weekdays %s in the %s week of %s' % (
            ', '.join(WEEKDAYS[i - 1] for i in self.weekdays), WEEK_NUMBERS[self.week_number-1], MONTHS[self.month-1]
        )


class AbsoluteMonthlyPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa493844(v=exchg.150).aspx
    ELEMENT_NAME = 'AbsoluteMonthlyRecurrence'

    FIELDS = [
        # Interval, in months, in range 1 -> 99
        IntegerField('interval', field_uri='t:Interval', min=1, max=99),
        # The day of month of an occurrence, in range 1 -> 31. If a particular month has less days than the day_of_month
        # value, the last day in the month is assumed
        IntegerField('day_of_month', field_uri='t:DayOfMonth', min=1, max=31),
    ]

    def __str__(self):
        return 'Occurs on the %s. day of every %s. month' % (self.day_of_month, self.interval)


class RelativeMonthlyPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa564558(v=exchg.150).aspx
    ELEMENT_NAME = 'RelativeMonthlyRecurrence'

    FIELDS = [
        # Interval, in months, in range 1 -> 99
        IntegerField('interval', field_uri='t:Interval', min=1, max=99),
        # Week number of the month, in range 1 -> 5. If 5 is specified, this assumes the last week of the month for
        # months that have only 4 weeks.
        EnumField('week_number', field_uri='t:DayOfWeekIndex', enum=WEEK_NUMBERS),
        # List of valid ISO 8601 weekdays, as list of numbers in range 1 -> 7 (1 being Monday). Alternatively, weekdays
        # can be one of the DAY (or 8), WEEK_DAY (or 9) or WEEKEND_DAY (or 10) consts which is interpreted as the first
        # day, weekday, or weekend day in the month, respectively.
        ExtraWeekdaysField('weekdays', field_uri='t:DaysOfWeek'),
    ]

    def __str__(self):
        return 'Occurs on weekdays %s in the %s week of every %s. month' % (
            ', '.join(WEEKDAYS[i - 1] for i in self.weekdays), WEEK_NUMBERS[self.week_number-1], self.interval
        )


class WeeklyPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa563500(v=exchg.150).aspx
    ELEMENT_NAME = 'WeeklyRecurrence'

    FIELDS = [
        # Interval, in weeks, in range 1 -> 99
        IntegerField('interval', field_uri='t:Interval', min=1, max=99),
        # List of valid ISO 8601 weekdays, as list of numbers in range 1 -> 7 (1 being Monday)
        EnumListField('weekdays', field_uri='t:DaysOfWeek', enum=WEEKDAYS),
        # The first day of the week. Defaults to Monday
        EnumField('first_day_of_week', field_uri='t:FirstDayOfWeek', enum=WEEKDAYS, default=1),
    ]

    def __str__(self):
        return 'Occurs on weekdays %s of every %s. week where the first day of the week is %s' % (
            ', '.join(WEEKDAYS[i - 1] for i in self.weekdays), self.interval, WEEKDAYS[self.first_day_of_week-1]
        )


class DailyPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa563228(v=exchg.150).aspx
    ELEMENT_NAME = 'DailyRecurrence'

    FIELDS = [
        # Interval, in days, in range 1 -> 999
        IntegerField('interval', field_uri='t:Interval', min=1, max=999),
    ]

    def __str__(self):
        return 'Occurs every %s. day' % self.interval


class NoEndPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa564699(v=exchg.150).aspx
    ELEMENT_NAME = 'NoEndRecurrence'

    FIELDS = [
        # Start date, as EWSDate
        DateField('start', field_uri='t:StartDate'),
    ]


class EndDatePattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa564536(v=exchg.150).aspx
    ELEMENT_NAME = 'EndDateRecurrence'

    FIELDS = [
        # Start date, as EWSDate
        DateField('start', field_uri='t:StartDate'),
        # End date, as EWSDate
        DateField('end', field_uri='t:EndDate'),
    ]


class NumberedPattern(Pattern):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa580960(v=exchg.150).aspx
    ELEMENT_NAME = 'NumberedRecurrence'

    FIELDS = [
        # Start date, as EWSDate
        DateField('start', field_uri='t:StartDate'),
        # The number of occurrences in this pattern
        IntegerField('number', field_uri='t:NumberOfOccurrences', min=0),
    ]


class Occurrence(EWSElement):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa565603(v=exchg.150).aspx
    ELEMENT_NAME = 'Occurrence'

    FIELDS = [
        # The item_id and changekey of a modified item occurrence
        EWSElementField('item', value_cls=ItemId, is_read_only=True),
        # The modified start time of the item, as EWSDateTime
        DateTimeField('start', field_uri='t:Start'),
        # The modified end time of the item, as EWSDateTime
        DateTimeField('end', field_uri='t:End'),
        # The original start time of the item, as EWSDateTime
        DateTimeField('original_start', field_uri='t:OriginalStart'),
    ]

# Container elements:
# 'ModifiedOccurrences'
# 'DeletedOccurrences'


class FirstOccurrence(Occurrence):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa565661(v=exchg.150).aspx
    ELEMENT_NAME = 'FirstOccurrence'


class LastOccurrence(Occurrence):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa565375(v=exchg.150).aspx
    ELEMENT_NAME = 'LastOccurrence'


class DeletedOccurrence(EWSElement):
    # MSDN: https://msdn.microsoft.com/en-us/library/office/aa566477(v=exchg.150).aspx
    ELEMENT_NAME = 'DeletedOccurrence'

    FIELDS = [
        # The modified start time of the item, as EWSDateTime
        DateTimeField('start', field_uri='t:Start'),
    ]


class Recurrence(EWSElement):
    # This is where the fun begins!
    pass