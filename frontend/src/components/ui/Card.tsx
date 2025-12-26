import { HTMLAttributes, forwardRef } from 'react'
import { clsx } from 'clsx'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    hover?: boolean
}

const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className, hover, children, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={clsx(
                    'card p-6',
                    hover && 'hover:shadow-md transition-shadow duration-200 cursor-pointer',
                    className
                )}
                {...props}
            >
                {children}
            </div>
        )
    }
)

Card.displayName = 'Card'

export default Card
